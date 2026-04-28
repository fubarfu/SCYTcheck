#!/usr/bin/env python3
"""Modify ReviewPage.tsx for Phase 3 Frontend implementation - auto-load from video_id"""

import re

# Read the current file
with open('src/web/frontend/src/pages/ReviewPage.tsx', 'r') as f:
    content = f.read()

# 1. Add function to extract video_id from URL params before the ReviewPage export
url_parser_func = '''function getVideoIdFromUrl(): string | null {
  if (typeof window === "undefined") return null;
  const hash = window.location.hash;
  const reviewMatch = hash.match(/#\\/review\\?video_id=([^&]*)/);
  return reviewMatch ? decodeURIComponent(reviewMatch[1]) : null;
}

'''

# Find the point to insert - just before "export function ReviewPage"
export_review = content.find("export function ReviewPage")
if export_review > 0:
    content = content[:export_review] + url_parser_func + content[export_review:]

# 2. Find where syncsGroupingSettingsDraft is defined and add loadReviewContext before it
sync_grouping_pattern = r'(const syncGroupingSettingsDraft = \(session: ReviewSessionPayload\) => \{)'

load_review_context_func = '''const loadReviewContext = async (videoId: string) => {
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
        merged_timestamp: string;
        candidates: unknown[];
        groups: unknown[];
      };
      
      // Convert API response to ReviewSessionPayload
      const session: ReviewSessionPayload = {
        session_id: videoId,
        csv_path: context.video_url,
        source_type: "youtube_url",
        source_value: context.video_url,
        workspace: {
          video_id: context.video_id,
          display_title: `Review: ${context.video_url}`,
          reviewed_names: [],
        },
        candidates: context.candidates as Candidate[],
        groups: context.groups as CandidateGroup[],
        thresholds: {
          similarity_threshold: 80,
          recommendation_threshold: 70,
          spelling_influence: 50,
          temporal_influence: 50,
        },
      };
      
      setSelectedSession(session);
      setSelectedSessionId(videoId);
      syncGroupingSettingsDraft(session);
    } catch (error) {
      setLoadingError(error instanceof Error ? error.message : "Network error");
    }
  };

  '''

content = re.sub(
    sync_grouping_pattern,
    load_review_context_func + r'\1',
    content
)

# 3. Add useEffect to auto-load when component mounts and video_id is in URL
# Find the last useEffect and add the new one after it
# Look for the pattern of the last useEffect (the pagehide listener)
pagehide_useeffect_end = content.rfind('}, [reopenContext]);')
if pagehide_useeffect_end > 0:
    # Find the end of this useEffect
    next_char_pos = pagehide_useeffect_end + len('}, [reopenContext]);')
    
    # Add the new useEffect for auto-loading from video_id
    auto_load_effect = '''

  // Auto-load review context when navigated with video_id URL parameter
  useEffect(() => {
    const videoIdFromUrl = getVideoIdFromUrl();
    if (videoIdFromUrl) {
      void loadReviewContext(videoIdFromUrl);
    }
  }, []);
'''
    
    content = content[:next_char_pos] + auto_load_effect + content[next_char_pos:]

# Write the modified file
with open('src/web/frontend/src/pages/ReviewPage.tsx', 'w') as f:
    f.write(content)

print("Modified ReviewPage.tsx successfully")
