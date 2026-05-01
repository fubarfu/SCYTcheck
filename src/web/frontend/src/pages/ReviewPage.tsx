import { useEffect, useMemo, useRef, useState } from "react";
import { CandidateRow, type Candidate } from "../components/CandidateRow";
import { CandidateGroupCard, type CandidateGroup } from "../components/CandidateGroupCard";
import { GroupListItem } from "../components/GroupListItem";
import { FrameThumbnailModal } from "../components/FrameThumbnailModal";
import { GroupingSettingsPanel } from "../components/GroupingSettingsPanel";
import { ReviewFilterBar } from "../components/ReviewFilterBar";
import { SessionLoadErrorState } from "../components/SessionLoadErrorState";
import { EditHistoryPanel } from "../components/EditHistoryPanel";
import {
  applyGroupToggleState,
  deriveGroupToggleState,
  hydrateEditHistoryEntries,
  markRestoredHistoryEntry,
  reconcileGroupMutationState,
  selectEditHistoryEntry,
  updateGroupToggleState,
  initialReviewStoreState,
  type EditHistoryEntry,
  type GroupToggleState,
  type ReviewStoreState,
} from "../state/reviewStore";
import {
  selectFilteredCandidates,
  selectVisibleGroups,
  selectVisibleCandidateIds,
  type ReviewFilterState,
} from "../state/reviewSelectors";
import {
  clearDraggedCandidate,
  getDraggedCandidate,
  setDropCommitted,
  setHoveredGroupId,
  setHoveredNewGroupZone,
} from "../state/dragPayload";

const CANDIDATE_DRAG_MIME = "application/x-scyt-candidate";
const FALLBACK_DRAG_MIME = "text/plain";

interface ReviewSessionPayload {
  session_id: string;
  csv_path: string;
  source_type?: "local_file" | "youtube_url";
  source_value?: string;
  workspace?: {
    video_id?: string;
    display_title?: string;
    reviewed_names?: string[];
    run_count?: number;
  };
  candidates?: Candidate[];
  thresholds?: {
    similarity_threshold?: number;
    recommendation_threshold?: number;
    spelling_influence?: number;
    temporal_influence?: number;
  };
  groups?: CandidateGroup[];
}

interface HistoryListResponse {
  entries: EditHistoryEntry[];
}

interface GroupValidationFeedbackState {
  candidateId?: string | null;
  message: string;
  hint?: string | null;
  conflictGroupId?: string | null;
}

interface GroupingSettingsDraft {
  spellingRelaxation: number;
  temporalInfluence: number;
}

interface ReviewPageProps {
  reopenContext?: {
    historyId: string;
    warningMessages: string[];
    hydratedAt: string;
  } | null;
  autoCsvPath?: string | null;
  activeReviewVideoId?: string | null;
}

function parseCandidateFallbackPayload(raw: string): { candidate_id?: string; source_group_id?: string | null } | null {
  const text = raw.trim();
  if (!text.startsWith("{")) {
    return null;
  }
  try {
    const payload = JSON.parse(text) as {
      kind?: string;
      candidate_id?: string;
      source_group_id?: string | null;
    };
    if (payload.kind !== "candidate") {
      return null;
    }
    return {
      candidate_id: payload.candidate_id,
      source_group_id: payload.source_group_id ?? null,
    };
  } catch {
    return null;
  }
}

function getVideoIdFromUrl(): string | null {
  if (typeof window === "undefined") return null;
  const hash = window.location.hash;
  const reviewMatch = hash.match(/#\/review\?video_id=([^&]*)/);
  return reviewMatch ? decodeURIComponent(reviewMatch[1]) : null;
}

export function ReviewPage({ reopenContext = null, autoCsvPath = null, activeReviewVideoId = null }: ReviewPageProps) {
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<ReviewSessionPayload | null>(null);
  const [projectLocation, setProjectLocation] = useState<string | null>(null);
  const [csvPathInput, setCsvPathInput] = useState("");
  const [loadingError, setLoadingError] = useState<string | null>(null);
  const [isRecalculatingGroups, setIsRecalculatingGroups] = useState(false);
  const [hasPendingGroupingSettings, setHasPendingGroupingSettings] = useState(false);
  const [exportMessage, setExportMessage] = useState<string | null>(null);
  const [showRecalculateConfirm, setShowRecalculateConfirm] = useState(false);
  const [undoCount, setUndoCount] = useState(0);
  const [groupToggles, setGroupToggles] = useState<GroupToggleState>({});
  const [groupValidationFeedback, setGroupValidationFeedback] = useState<Record<string, GroupValidationFeedbackState>>({});
  const [newGroupDropActive, setNewGroupDropActive] = useState(false);
  const [groupingSettingsDraft, setGroupingSettingsDraft] = useState<GroupingSettingsDraft>({
    spellingRelaxation: 50,
    temporalInfluence: 50,
  });
  const [filter, setFilter] = useState<ReviewFilterState>({
    searchText: "",
    status: "all",
  });
  const [storeState, setStoreState] = useState<ReviewStoreState>(initialReviewStoreState);

  const [thumbnailCandidateId, setThumbnailCandidateId] = useState<string | null>(null);
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null);
  const [reopenWarning, setReopenWarning] = useState<string | null>(null);
  const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
  const [videoContextRunCount, setVideoContextRunCount] = useState<number | null>(null);
  const autoLoadedHistoryCsvPathRef = useRef<string | null>(null);
  const latestSessionFetchTokenRef = useRef(0);
  const autoLoadedVideoIdRef = useRef<string | null>(null);

  const sourceType = selectedSession?.source_type ?? "local_file";
  const sourceValue = selectedSession?.source_value ?? "";
  const videoId = selectedSession?.workspace?.video_id?.trim() ?? "";
  const isVideoContextSession = Boolean(videoId) && selectedSessionId === videoId;
  const selectedHistoryEntryId = storeState.editHistory.selectedEntryId;

  const selectedCandidate = useMemo(
    () => (thumbnailCandidateId
      ? selectedSession?.candidates?.find((c) => c.candidate_id === thumbnailCandidateId) ?? null
      : null),
    [thumbnailCandidateId, selectedSession?.candidates],
  );
  const filteredCandidates = useMemo(
    () => selectFilteredCandidates(selectedSession?.candidates ?? [], filter),
    [selectedSession?.candidates, filter],
  );
  const visibleCandidateIds = useMemo(
    () => new Set(selectVisibleCandidateIds(selectedSession?.candidates ?? [], filter)),
    [selectedSession?.candidates, filter],
  );
  const visibleGroups = useMemo(() => {
    const hydratedGroups = selectedSession
      ? applyGroupToggleState(selectedSession, groupToggles).groups ?? []
      : [];
    return selectVisibleGroups(
      hydratedGroups as CandidateGroup[],
      selectedSession?.candidates ?? [],
      filter,
    );
  }, [selectedSession, selectedSession?.candidates, groupToggles, filter]);
  const similarityThreshold = selectedSession?.thresholds?.similarity_threshold ?? 80;
  const recommendationThreshold = selectedSession?.thresholds?.recommendation_threshold ?? 70;
  const appliedSpellingRelaxation = 100 - (selectedSession?.thresholds?.spelling_influence ?? 50);
  const appliedTemporalInfluence = selectedSession?.thresholds?.temporal_influence ?? 50;
  const spellingRelaxation = groupingSettingsDraft.spellingRelaxation;
  const temporalInfluence = groupingSettingsDraft.temporalInfluence;
  const totalGroups = selectedSession?.groups?.length ?? 0;
  const resolvedGroups = useMemo(
    () => (selectedSession?.groups ?? []).filter((group) => (group.resolution_status ?? "UNRESOLVED") === "RESOLVED").length,
    [selectedSession?.groups],
  );
  const reviewedCandidateCount = useMemo(
    () => (selectedSession?.candidates ?? []).filter((candidate) => (candidate.status ?? "pending") !== "pending").length,
    [selectedSession?.candidates],
  );
  const newCandidateCount = useMemo(
    () => (selectedSession?.candidates ?? []).filter((candidate) => Boolean(candidate.marked_new)).length,
    [selectedSession?.candidates],
  );
  const runCount = useMemo(() => {
    const raw = (selectedSession as { workspace?: { run_count?: unknown } } | null)?.workspace?.run_count;
    const parsed = Number(raw);
    if (Number.isFinite(parsed) && parsed > 0) {
      return Math.floor(parsed);
    }
    if (videoContextRunCount && videoContextRunCount > 0) {
      return Math.floor(videoContextRunCount);
    }
    return null;
  }, [selectedSession, videoContextRunCount]);



  const loadReviewContext = async (videoId: string) => {
    try {
      setLoadingError(null);
      const resp = await fetch(`/api/review/context?video_id=${encodeURIComponent(videoId)}`);
      if (!resp.ok) {
        const error = await resp.json().catch(() => ({})) as { message?: string };
        setLoadingError(error.message ?? "Failed to load review context");
        return;
      }
      const context = await resp.json() as {
        video_id: string;
        video_url: string;
        run_count?: unknown;
        merged_timestamp: string;
        project_location?: string;
        thresholds?: {
          similarity_threshold?: number;
          recommendation_threshold?: number;
          spelling_influence?: number;
          temporal_influence?: number;
        };
        candidates: Array<{
          id: string;
          spelling: string;
          corrected_text?: string;
          discovered_in_run?: string;
          marked_new?: boolean;
          decision?: "unreviewed" | "confirmed" | "rejected" | "edited";
          start_timestamp?: string;
        }>;
        groups: Array<{
          id: string;
          name?: string;
          candidate_ids?: string[];
          decision?: "unreviewed" | "confirmed" | "rejected";
        }>;
      };

      const candidates: Candidate[] = context.candidates.map((candidate) => ({
        candidate_id: candidate.id,
        extracted_name: candidate.spelling,
        corrected_text: candidate.corrected_text,
        status: candidate.decision === "unreviewed" || !candidate.decision ? "pending" : candidate.decision,
        marked_new: Boolean(candidate.marked_new),
        start_timestamp: candidate.start_timestamp ?? "",
      }));

      const candidateById = new Map(candidates.map((candidate) => [candidate.candidate_id, candidate]));
      const groups: CandidateGroup[] = context.groups.map((group) => {
        const groupCandidates = (group.candidate_ids ?? [])
          .map((candidateId) => candidateById.get(candidateId))
          .filter((candidate): candidate is Candidate => Boolean(candidate));

        return {
          group_id: group.id,
          display_name: group.name ?? group.id,
          resolution_status: group.decision === "confirmed" ? "RESOLVED" : "UNRESOLVED",
          candidates: groupCandidates,
          total_candidate_count: groupCandidates.length,
          active_candidate_count: groupCandidates.length,
          occurrence_count: groupCandidates.length,
          accepted_name: group.decision === "confirmed" ? group.name ?? null : null,
          accepted_name_summary: group.decision === "confirmed" ? group.name ?? null : null,
        };
      });
      const contextRunCount = Number(context.run_count);
      const parsedContextRunCount = Number.isFinite(contextRunCount) && contextRunCount > 0
        ? Math.floor(contextRunCount)
        : null;

      const session: ReviewSessionPayload = {
        session_id: videoId,
        csv_path: context.video_url,
        source_type: "youtube_url",
        source_value: context.video_url,
        workspace: {
          video_id: context.video_id,
          display_title: `Review: ${context.video_url}`,
          reviewed_names: [],
          run_count: parsedContextRunCount ?? undefined,
        },
        candidates,
        groups,
        thresholds: {
          similarity_threshold: context.thresholds?.similarity_threshold ?? 80,
          recommendation_threshold: context.thresholds?.recommendation_threshold ?? 70,
          spelling_influence: context.thresholds?.spelling_influence ?? 50,
          temporal_influence: context.thresholds?.temporal_influence ?? 50,
        },
      };
      
      setSelectedSession(session);
      setVideoContextRunCount(parsedContextRunCount);
      setSelectedSessionId(videoId);
      setProjectLocation(context.project_location ?? null);
      syncGroupingSettingsDraft(session);
    } catch (error) {
      setLoadingError(error instanceof Error ? error.message : "Network error");
    }
  };

  const syncGroupingSettingsDraft = (session: ReviewSessionPayload) => {
    const spellingInfluence = session.thresholds?.spelling_influence ?? 50;
    setGroupingSettingsDraft({
      spellingRelaxation: 100 - spellingInfluence,
      temporalInfluence: session.thresholds?.temporal_influence ?? 50,
    });
    setHasPendingGroupingSettings(false);
  };

  useEffect(() => {
    const openReview = (event: Event) => {
      const custom = event as CustomEvent<{ csvPath?: string; autoLoad?: boolean }>;
      const csvPath = custom.detail?.csvPath;
      if (csvPath) {
        setCsvPathInput(csvPath);
        if (custom.detail?.autoLoad) {
          void loadSessionFromCsv(csvPath);
        }
      }
    };
    window.addEventListener("scyt:open-review", openReview as EventListener);
    return () => window.removeEventListener("scyt:open-review", openReview as EventListener);
  }, []);

  useEffect(() => {
    const value = autoCsvPath?.trim() ?? "";
    if (value) {
      setCsvPathInput(value);
    }
  }, [autoCsvPath]);

  useEffect(() => {
    const value = autoCsvPath?.trim() ?? "";
    if (!reopenContext || !value) {
      return;
    }
    const activeVideoId = activeReviewVideoId?.trim() ?? "";
    if (activeVideoId) {
      // Project-open flows should hydrate via video context, not CSV session loading.
      return;
    }
    const scheduleId = window.setTimeout(() => {
      const videoIdFromUrl = getVideoIdFromUrl();
      if (videoIdFromUrl) {
        // When opening a project through #/review?video_id=..., prefer project context
        // and avoid overriding it with a CSV session auto-load.
        return;
      }
      if (autoLoadedHistoryCsvPathRef.current === value) {
        return;
      }
      autoLoadedHistoryCsvPathRef.current = value;
      void loadSessionFromCsv(value);
    }, 150);
    return () => {
      window.clearTimeout(scheduleId);
    };
  }, [autoCsvPath, reopenContext, activeReviewVideoId]);

  useEffect(() => {
    const activeVideoId = activeReviewVideoId?.trim() ?? "";
    if (!activeVideoId) {
      return;
    }
    if (autoLoadedVideoIdRef.current === activeVideoId) {
      return;
    }
    autoLoadedVideoIdRef.current = activeVideoId;
    void loadReviewContext(activeVideoId);
  }, [activeReviewVideoId]);

  useEffect(() => {
    if (!reopenContext) {
      setReopenWarning(null);
      return;
    }
    if (reopenContext.warningMessages.length > 0) {
      setReopenWarning(reopenContext.warningMessages.join(" "));
      return;
    }
    setReopenWarning(null);
  }, [reopenContext]);

  // Auto-load review context whenever the review hash carries a video_id.
  useEffect(() => {
    const syncReviewContextFromHash = () => {
      const videoIdFromUrl = getVideoIdFromUrl();
      if (!videoIdFromUrl) {
        return;
      }
      if (autoLoadedVideoIdRef.current === videoIdFromUrl) {
        return;
      }
      autoLoadedVideoIdRef.current = videoIdFromUrl;
      void loadReviewContext(videoIdFromUrl);
    };

    syncReviewContextFromHash();
    window.addEventListener("hashchange", syncReviewContextFromHash);
    return () => {
      window.removeEventListener("hashchange", syncReviewContextFromHash);
    };
  }, []);


  useEffect(() => {
    const sessionId = selectedSessionId?.trim() ?? "";
    if (!sessionId) {
      return;
    }
    const endpoint = `/api/review/sessions/${encodeURIComponent(sessionId)}/flush-on-close`;
    const flushOnClose = () => {
      if (navigator.sendBeacon) {
        navigator.sendBeacon(endpoint);
        return;
      }
      void fetch(endpoint, { method: "POST", keepalive: true });
    };

    window.addEventListener("pagehide", flushOnClose);
    window.addEventListener("beforeunload", flushOnClose);
    return () => {
      window.removeEventListener("pagehide", flushOnClose);
      window.removeEventListener("beforeunload", flushOnClose);
    };
  }, [selectedSessionId]);

  useEffect(() => {
    if (!selectedSessionId || !videoId) {
      setStoreState((prev) => ({
        ...prev,
        editHistory: {
          ...prev.editHistory,
          entries: [],
          selectedEntryId: null,
          restoredEntryId: null,
          loading: false,
          error: null,
        },
      }));
      return;
    }
    if (isVideoContextSession) {
      setStoreState((prev) => ({
        ...prev,
        editHistory: {
          ...prev.editHistory,
          entries: [],
          selectedEntryId: null,
          restoredEntryId: null,
          loading: false,
          error: null,
        },
      }));
      return;
    }
    setStoreState((prev) => ({
      ...prev,
      editHistory: {
        ...prev.editHistory,
        loading: true,
        error: null,
      },
    }));
    void fetchEditHistory(videoId, selectedSessionId);
  }, [selectedSessionId, videoId, isVideoContextSession]);

  // Keep selectedGroupId valid: prefer an unresolved group (with validation error first),
  // then any visible group. Reset to null when no groups remain.
  useEffect(() => {
    if (visibleGroups.length === 0) {
      if (selectedGroupId !== null) {
        setSelectedGroupId(null);
      }
      return;
    }
    const stillVisible = selectedGroupId
      ? visibleGroups.some((g) => g.group_id === selectedGroupId)
      : false;
    if (stillVisible) {
      return;
    }
    const errorGroup = visibleGroups.find((g) => Boolean(groupValidationFeedback[g.group_id]));
    const unresolved = visibleGroups.find((g) => (g.resolution_status ?? "UNRESOLVED") !== "RESOLVED");
    const next = errorGroup ?? unresolved ?? visibleGroups[0];
    setSelectedGroupId(next.group_id);
  }, [visibleGroups, selectedGroupId, groupValidationFeedback]);

  const loadSessionFromCsv = async (csvPathOverride?: string) => {
    setLoadingError(null);
    setExportMessage(null);
    setVideoContextRunCount(null);
    const targetPath = (csvPathOverride ?? csvPathInput).trim();
    if (!targetPath) {
      setLoadingError("csv_path is required");
      return;
    }
    const resp = await fetch("/api/review/sessions/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ csv_path: targetPath }),
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({ message: "Unable to load session" })) as { message?: string };
      setLoadingError(err.message ?? "Unable to load session");
      return;
    }
    const body = await resp.json() as { session_id: string };
    setHasPendingGroupingSettings(false);
    setSelectedSessionId(body.session_id);
    await fetchSession(body.session_id, { syncGroupingSettingsDraft: true });
  };

  const fetchSession = async (sessionId: string, options?: { syncGroupingSettingsDraft?: boolean }) => {
    const normalizedSessionId = sessionId.trim();
    if (!normalizedSessionId) {
      return;
    }
    const fetchToken = ++latestSessionFetchTokenRef.current;
    const resp = await fetch(`/api/review/sessions/${normalizedSessionId}?_ts=${Date.now()}`, { cache: "no-store" });
    if (!resp.ok) return;
    const session = await resp.json() as ReviewSessionPayload;
    if (fetchToken !== latestSessionFetchTokenRef.current) {
      return;
    }
    const reconciled = reconcileGroupMutationState(session);
    const nextToggles = deriveGroupToggleState(reconciled.groups ?? []);
    setGroupToggles(nextToggles);
    setSelectedSession(applyGroupToggleState(reconciled, nextToggles));
    if (options?.syncGroupingSettingsDraft) {
      syncGroupingSettingsDraft(reconciled);
    }
    setGroupValidationFeedback({});
    setSelectedSessionId(normalizedSessionId);
    setLoadingError(null);
  };

  const fetchEditHistory = async (workspaceVideoId: string, sessionId: string) => {
    const resp = await fetch(
      `/api/review/workspaces/${encodeURIComponent(workspaceVideoId)}/history?session_id=${encodeURIComponent(sessionId)}`,
    );
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({ message: "Unable to load edit history" })) as { message?: string };
      setStoreState((prev) => ({
        ...prev,
        editHistory: {
          ...prev.editHistory,
          entries: [],
          loading: false,
          error: body.message ?? "Unable to load edit history",
        },
      }));
      return;
    }
    const body = await resp.json() as HistoryListResponse;
    setStoreState((prev) => hydrateEditHistoryEntries(prev, body.entries ?? []));
  };

  const restoreHistoryEntry = async (entryId: string) => {
    if (!selectedSessionId || !videoId) {
      return;
    }
    const resp = await fetch(
      `/api/review/workspaces/${encodeURIComponent(videoId)}/history/${encodeURIComponent(entryId)}/restore`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: selectedSessionId }),
      },
    );
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({ message: "Restore failed" })) as { message?: string };
      setLoadingError(body.message ?? "Restore failed");
      return;
    }
    setStoreState((prev) => markRestoredHistoryEntry(prev, entryId));
    setLoadingError(null);
    setExportMessage("Snapshot restored. Review state has been reloaded.");
    await fetchSession(selectedSessionId, { syncGroupingSettingsDraft: true });
    await fetchEditHistory(videoId, selectedSessionId);
  };

  const postAction = async (action: { action_type: string; target_ids: string[]; payload?: Record<string, unknown> }) => {
    if (!selectedSessionId) return;
    setExportMessage(null);
    const actionGroupId = String(action.payload?.group_id ?? "").trim();
    const actionCandidateId = action.target_ids[0] ?? null;

    if (isVideoContextSession && videoId) {
      const mappedAction = action.action_type === "confirm"
        ? "confirmed"
        : action.action_type === "reject"
          ? "rejected"
          : action.action_type === "edit"
            ? "edited"
            : action.action_type === "clear_new"
              ? "clear_new"
              : action.action_type === "deselect"
                ? "unreviewed"
              : null;

      if (mappedAction) {
        const targetCandidateIds = mappedAction === "unreviewed" && actionGroupId
          ? ((selectedSession?.groups ?? [])
            .find((group) => group.group_id === actionGroupId)
            ?.candidates
            .map((candidate) => candidate.candidate_id) ?? [])
          : (actionCandidateId ? [actionCandidateId] : []);

        if (targetCandidateIds.length === 0) {
          setLoadingError(`Action ${action.action_type} has no candidate target in project review mode.`);
          return;
        }

        for (const targetId of targetCandidateIds) {
          const resp = await fetch("/api/review/action", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              video_id: videoId,
              candidate_id: targetId,
              action: mappedAction,
              user_note: typeof action.payload?.corrected_text === "string"
                ? action.payload.corrected_text
                : undefined,
            }),
          });
          if (!resp.ok) {
            const errorBody = await resp.json().catch(() => ({ message: "Action failed" })) as { message?: string };
            setLoadingError(errorBody.message ?? "Action failed");
            return;
          }
        }
        setLoadingError(null);
        setUndoCount((value) => value + 1);
        await loadReviewContext(videoId);
        return;
      }

      setLoadingError(`Action ${action.action_type} is not available in project review mode.`);
      return;
    }

    if (action.action_type === "toggle_collapse") {
      const groupId = String(action.payload?.group_id ?? "").trim();
      const requested = action.payload?.is_collapsed;
      if (groupId && typeof requested === "boolean") {
        setGroupToggles((previous) => {
          const nextToggles = updateGroupToggleState(previous, groupId, requested);
          setSelectedSession((prev) => {
            if (!prev) {
              return prev;
            }
            return applyGroupToggleState(prev, nextToggles);
          });
          return nextToggles;
        });
      }
    }

    const resp = await fetch(`/api/review/sessions/${selectedSessionId}/actions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(action),
    });
    if (!resp.ok) {
      const errorBody = await resp.json().catch(() => null) as {
        message?: string;
        validation?: {
          is_valid?: boolean;
          message?: string;
          hint?: string;
          conflict_group_id?: string;
        };
        action?: {
          group_id?: string;
          candidate_id?: string;
        };
      } | null;

      const validation = errorBody?.validation;
      const responseGroupId = String(errorBody?.action?.group_id ?? actionGroupId).trim();
      if (resp.status === 422 && validation && responseGroupId) {
        setGroupValidationFeedback((previous) => ({
          ...previous,
          [responseGroupId]: {
            candidateId: errorBody?.action?.candidate_id ?? actionCandidateId,
            message: validation.message ?? errorBody?.message ?? "Validation failed",
            hint: validation.hint ?? null,
            conflictGroupId: validation.conflict_group_id ?? null,
          },
        }));
        setLoadingError(null);
        await fetchSession(selectedSessionId);
        return;
      }
      setLoadingError(errorBody?.message ?? "Action failed");
      return;
    }
    if (actionGroupId) {
      setGroupValidationFeedback((previous) => {
        if (!(actionGroupId in previous)) {
          return previous;
        }
        const next = { ...previous };
        delete next[actionGroupId];
        return next;
      });
    }
    setLoadingError(null);
    setUndoCount((v) => v + 1);
    await fetchSession(selectedSessionId);
    if (videoId) {
      await fetchEditHistory(videoId, selectedSessionId);
    }
  };

  const recalculateGroups = async () => {
    if (!selectedSessionId || isRecalculatingGroups) {
      return;
    }

    setIsRecalculatingGroups(true);
    setExportMessage(null);
    setGroupValidationFeedback({});
    setLoadingError(null);
    try {
      const normalizedSessionId = selectedSessionId.trim();
      if (!normalizedSessionId) {
        setLoadingError("No session selected");
        return;
      }
      const thresholdPayload = {
        similarity_threshold: similarityThreshold,
        recommendation_threshold: recommendationThreshold,
        spelling_influence: 100 - spellingRelaxation,
        temporal_influence: temporalInfluence,
      };
      if (isVideoContextSession && videoId) {
        const groupedResp = await fetch("/api/review/grouping", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            video_id: videoId,
            ...thresholdPayload,
            reset_decisions: true,
          }),
        });
        if (!groupedResp.ok) {
          setLoadingError("Unable to update grouping settings");
          return;
        }
        await loadReviewContext(videoId);
        setUndoCount(0);
        return;
      }
      const thresholdsChanged = spellingRelaxation !== appliedSpellingRelaxation
        || temporalInfluence !== appliedTemporalInfluence;
      if (thresholdsChanged) {
        const thresholdsResp = await fetch(`/api/review/sessions/${normalizedSessionId}/thresholds`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(thresholdPayload),
        });
        if (!thresholdsResp.ok) {
          setLoadingError("Unable to update grouping settings");
          return;
        }
      }
      const resp = await fetch(`/api/review/sessions/${normalizedSessionId}/recalculate`, {
        method: "POST",
      });
      if (!resp.ok) {
        setLoadingError("Unable to recalculate groups");
        return;
      }
      const session = await resp.json() as ReviewSessionPayload;
      const reconciled = reconcileGroupMutationState(session);
      setSelectedSession(reconciled);
      syncGroupingSettingsDraft(reconciled);
      setUndoCount(0);
    } finally {
      setIsRecalculatingGroups(false);
    }
  };

  const requestRecalculateGroups = () => {
    if (!selectedSessionId || isRecalculatingGroups) {
      return;
    }
    setShowRecalculateConfirm(true);
  };

  const handleUndo = async () => {
    if (!selectedSessionId) return;
    setExportMessage(null);
    const resp = await fetch(`/api/review/sessions/${selectedSessionId}/undo`, { method: "POST" });
    if (!resp.ok) {
      setLoadingError("Undo failed");
      return;
    }
    const body = await resp.json() as { remaining_undo_count: number };
    setUndoCount(body.remaining_undo_count);
    await fetchSession(selectedSessionId);
    if (videoId) {
      await fetchEditHistory(videoId, selectedSessionId);
    }
  };

  const openThumbnail = async (candidateId: string) => {
    if (!selectedSessionId) return;
    const plParam = projectLocation ? `?pl=${encodeURIComponent(projectLocation)}` : "";
    const resp = await fetch(`/api/review/sessions/${selectedSessionId}/thumbnails/${candidateId}${plParam}`);
    if (resp.ok) {
      const body = await resp.json().catch(() => ({})) as { thumbnail_url?: string };
      setThumbnailUrl(body.thumbnail_url ?? `/api/review/sessions/${selectedSessionId}/thumbnails/${candidateId}.png${plParam}`);
    } else {
      setThumbnailUrl(null);
    }
    setThumbnailCandidateId(candidateId);
  };

  const exportSession = async () => {
    if (!selectedSessionId) return;
    setExportMessage(null);
    const resp = await fetch(`/api/review/sessions/${selectedSessionId}/export`, { method: "POST" });
    if (!resp.ok) {
      setLoadingError("Export failed");
      return;
    }
    const body = await resp.json() as { deduplicated_names_csv_path: string; occurrences_csv_path: string };
    setExportMessage(
      `Exported deduplicated names to ${body.deduplicated_names_csv_path} and occurrences to ${body.occurrences_csv_path}`,
    );
  };

  const handleDropCandidateIntoNewGroup = (rawPayload: string) => {
    const parsed = parseCandidateFallbackPayload(rawPayload);
    if (!parsed) {
      return;
    }
    const candidateId = String(parsed.candidate_id ?? "").trim();
    if (!candidateId) {
      return;
    }
    void postAction({
      action_type: "move_candidate",
      target_ids: [candidateId],
      payload: {
        candidate_id: candidateId,
        source_group_id: parsed.source_group_id ?? null,
        create_new_group: true,
      },
    });
  };

  return (
    <section className="page-panel">
      <div className="page-heading-row">
        <p className="eyebrow">Review</p>
        <h2>Review detected names</h2>
        <p className="page-subtitle">
          Review the merged video context, filter what matters, then confirm or reject candidates without the extra noise.
        </p>
      </div>

      {loadingError && <SessionLoadErrorState message={loadingError} onRetry={() => setLoadingError(null)} />}
      {exportMessage && (
        <div className="export-banner" role="status">
          <div className="export-banner-row">
            <span>{exportMessage}</span>
            <button
              type="button"
              className="export-banner-close"
              aria-label="Dismiss message"
              onClick={() => setExportMessage(null)}
            >
              <span className="material-symbols-outlined" aria-hidden="true">close</span>
            </button>
          </div>
        </div>
      )}
      {reopenWarning && <div className="export-banner">{reopenWarning}</div>}
      {hasPendingGroupingSettings && (
        <div className="export-banner">
          Grouping settings changed. Click Recalculate in Grouping settings to apply them to existing groups.
        </div>
      )}

      <div className="review-stack">
        <div className="panel-card">
          <div className="panel-card-body review-topbar">
            <div className="review-source-picker">
              {videoId ? (
                <>
                  <label>
                    Video URL
                    <input type="text" value={sourceValue} readOnly />
                  </label>
                  <label>
                    Project ID
                    <input type="text" value={videoId} readOnly />
                  </label>
                </>
              ) : (
                <label>
                  Result file
                  <div className="review-load-row">
                    <input
                      type="text"
                      value={csvPathInput}
                      onChange={(e) => setCsvPathInput(e.target.value)}
                      placeholder="C:/output/match.csv"
                    />
                    <button type="button" className="primary-action" onClick={() => { void loadSessionFromCsv(); }}>
                      Load result
                    </button>
                  </div>
                </label>
              )}

            </div>

            <div className="review-summary-block">
              <div className="review-quick-stats" aria-label="Session quick stats">
                <div className="review-quick-stat">
                  <span className="review-quick-stat-label">Analysis runs</span>
                  <strong>{runCount ?? "--"}</strong>
                </div>
                <div className="review-quick-stat">
                  <span className="review-quick-stat-label">Reviewed</span>
                  <strong>{reviewedCandidateCount}</strong>
                </div>
                <div className="review-quick-stat">
                  <span className="review-quick-stat-label">New</span>
                  <strong>{newCandidateCount}</strong>
                </div>
              </div>
              <div className="review-progress-meta">
                <span>{resolvedGroups} / {totalGroups} resolved</span>
                <span>{filteredCandidates.length} visible</span>
              </div>
              <progress
                className="review-progress-track"
                value={resolvedGroups}
                max={Math.max(totalGroups, 1)}
              />
              <div className="candidate-list-actions">
                <button
                  type="button"
                  className="ghost-action"
                  onClick={() => { void handleUndo(); }}
                  disabled={undoCount <= 0}
                >
                  Undo
                </button>
                <button type="button" className="primary-action" onClick={() => { void exportSession(); }} disabled={!selectedSessionId}>
                  Export review
                </button>
              </div>
            </div>
          </div>
        </div>

        <div className="panel-card">
          <div className="panel-card-body review-filter-shell">
            <ReviewFilterBar
              searchText={filter.searchText}
              status={filter.status}
              onSearchTextChange={(value) => setFilter((prev) => ({ ...prev, searchText: value }))}
              onStatusChange={(value) => setFilter((prev) => ({ ...prev, status: value }))}
            />
          </div>
        </div>

        <div className="review-workspace">
          <aside className="review-group-rail" aria-label="Candidate groups">
            <div className="group-rail-header">
              <span className="group-rail-header-title">Groups</span>
              <span className="group-rail-header-count">{visibleGroups.length}</span>
            </div>
            <div
              className={`new-group-dropzone${newGroupDropActive ? " is-active" : ""}`}
              onDragOver={(event) => {
                const types = Array.from(event.dataTransfer.types);
                const hasCandidateMime = types.includes(CANDIDATE_DRAG_MIME);
                const fallbackPayload = parseCandidateFallbackPayload(event.dataTransfer.getData(FALLBACK_DRAG_MIME));
                const hasActiveCandidate = Boolean(getDraggedCandidate());
                if (!hasCandidateMime && !fallbackPayload && !hasActiveCandidate) {
                  return;
                }
                event.preventDefault();
                event.dataTransfer.dropEffect = "move";
                setHoveredGroupId(null);
                setHoveredNewGroupZone(true);
                setNewGroupDropActive(true);
              }}
              onDragLeave={() => {
                setHoveredNewGroupZone(false);
                setNewGroupDropActive(false);
              }}
              onDrop={(event) => {
                event.preventDefault();
                setHoveredNewGroupZone(false);
                setNewGroupDropActive(false);
                const payload = event.dataTransfer.getData(CANDIDATE_DRAG_MIME).trim()
                  || event.dataTransfer.getData(FALLBACK_DRAG_MIME).trim()
                  || (() => {
                    const active = getDraggedCandidate();
                    return active ? JSON.stringify({ kind: "candidate", ...active }) : "";
                  })();
                handleDropCandidateIntoNewGroup(payload);
                setDropCommitted(true);
                clearDraggedCandidate();
              }}
            >
              Drop candidate here to create a new group
            </div>
            <div className="group-rail-list">
              {visibleGroups.length === 0 ? (
                <p className="group-rail-empty">No groups match the current filters.</p>
              ) : (
                visibleGroups.map((group) => (
                  <GroupListItem
                    key={group.group_id}
                    group={group}
                    isSelected={group.group_id === selectedGroupId}
                    hasValidationError={Boolean(groupValidationFeedback[group.group_id])}
                    onSelect={setSelectedGroupId}
                    onMergeGroups={(sourceGroupId, targetGroupId) => {
                      void postAction({
                        action_type: "merge_groups",
                        target_ids: [sourceGroupId],
                        payload: {
                          source_group_id: sourceGroupId,
                          target_group_id: targetGroupId,
                          group_id: targetGroupId,
                        },
                      });
                    }}
                    onMoveCandidate={(candidateId, sourceGroupId, targetGroupId) => {
                      void postAction({
                        action_type: "move_candidate",
                        target_ids: [candidateId],
                        payload: {
                          candidate_id: candidateId,
                          source_group_id: sourceGroupId,
                          to_group_id: targetGroupId,
                          group_id: targetGroupId,
                        },
                      });
                    }}
                  />
                ))
              )}
            </div>
            <GroupingSettingsPanel
              spellingRelaxation={spellingRelaxation}
              temporalInfluence={temporalInfluence}
              isRecalculating={isRecalculatingGroups}
              disabled={!selectedSessionId}
              onSpellingRelaxationChange={(value) => {
                setGroupingSettingsDraft((previous) => ({ ...previous, spellingRelaxation: value }));
                setHasPendingGroupingSettings(value !== appliedSpellingRelaxation || temporalInfluence !== appliedTemporalInfluence);
              }}
              onTemporalInfluenceChange={(value) => {
                setGroupingSettingsDraft((previous) => ({ ...previous, temporalInfluence: value }));
                setHasPendingGroupingSettings(spellingRelaxation !== appliedSpellingRelaxation || value !== appliedTemporalInfluence);
              }}
              onRecalculate={requestRecalculateGroups}
            />
          </aside>

          <div className="review-workspace-pane">
            {filteredCandidates.length === 0 ? (
              <div className="panel-card">
                <div className="panel-card-body empty-region-state">
                  <div>
                    <strong>No candidates to review yet.</strong>
                    <p>{videoId ? "This video has no merged candidates yet, or the current filters removed them." : "Load a result file or adjust the current filters."}</p>
                  </div>
                </div>
              </div>
            ) : visibleGroups.length > 0 ? (
              (() => {
                const activeGroup = visibleGroups.find((g) => g.group_id === selectedGroupId) ?? visibleGroups[0];
                if (!activeGroup) {
                  return null;
                }
                return (
                  <CandidateGroupCard
                    key={activeGroup.group_id}
                    group={activeGroup}
                    selectedSessionId={selectedSessionId}
                    projectLocation={projectLocation}
                    sourceType={sourceType}
                    sourceValue={sourceValue}
                    validationFeedback={groupValidationFeedback[activeGroup.group_id] ?? null}
                    forceExpanded
                    hideCollapseControl
                    onAction={(action) => {
                      if (action.target_ids.length > 1) {
                        action.target_ids = action.target_ids.filter((id) => visibleCandidateIds.has(id));
                      }
                      void postAction(action);
                    }}
                    onOpenThumbnail={(id) => { void openThumbnail(id); }}
                  />
                );
              })()
            ) : (
              <div className="candidate-list review-candidate-stack">
                {filteredCandidates.map((c) => (
                  <CandidateRow
                    key={c.candidate_id}
                    candidate={c}
                    sourceType={sourceType}
                    sourceValue={sourceValue}
                    thumbnailCheckUrl={selectedSessionId ? `/api/review/sessions/${selectedSessionId}/thumbnails/${c.candidate_id}${projectLocation ? `?pl=${encodeURIComponent(projectLocation)}` : ""}` : null}
                    onAction={(action) => {
                      if (action.target_ids.length > 1) {
                        action.target_ids = action.target_ids.filter((id) => visibleCandidateIds.has(id));
                      }
                      void postAction(action);
                    }}
                    onOpenThumbnail={(id) => { void openThumbnail(id); }}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        <EditHistoryPanel
          entries={storeState.editHistory.entries}
          selectedEntryId={selectedHistoryEntryId}
          restoredEntryId={storeState.editHistory.restoredEntryId}
          busy={storeState.editHistory.loading}
          error={storeState.editHistory.error}
          onSelectEntry={(entryId) => {
            setStoreState((prev) => selectEditHistoryEntry(prev, entryId));
          }}
          onRestoreEntry={(entryId) => {
            void restoreHistoryEntry(entryId);
          }}
        />
      </div>

      {thumbnailCandidateId && (
        <FrameThumbnailModal
          candidateId={thumbnailCandidateId}
          thumbnailUrl={thumbnailUrl}
          metadata={{
            timestamp: selectedCandidate?.start_timestamp,
            sourceType,
          }}
          onClose={() => {
            setThumbnailCandidateId(null);
            setThumbnailUrl(null);
          }}
        />
      )}

      {showRecalculateConfirm && (
        <div className="modal-overlay" role="dialog" aria-modal="true" aria-label="Recalculate groups warning">
          <div className="modal-panel restore-confirmation-modal">
            <h3>Recalculate groups</h3>
            <p>
              Recalculate groups with current settings? This will reset your current review decisions
              (resolved/unresolved state, accepted/rejected selections, and manual grouping changes).
            </p>
            <div className="modal-actions">
              <button
                type="button"
                className="ghost-action"
                onClick={() => setShowRecalculateConfirm(false)}
                disabled={isRecalculatingGroups}
              >
                Cancel
              </button>
              <button
                type="button"
                className="primary-action"
                onClick={() => {
                  setShowRecalculateConfirm(false);
                  void recalculateGroups();
                }}
                disabled={isRecalculatingGroups}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}
