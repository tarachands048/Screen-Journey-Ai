import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN = process.env.NEXT_PUBLIC_TEAM_TOKEN ?? "";
if (!TOKEN) {
  console.warn("NEXT_PUBLIC_TEAM_TOKEN is not set. Copy frontend/.env.example to frontend/.env.local and set the token.");
}

const api = axios.create({
  baseURL: API_URL,
  headers: { "X-Team-Token": TOKEN },
});

// Sessions
export const getSessions = () => api.get("/api/sessions").then((r) => r.data);
export const getSession = (id: string) => api.get(`/api/sessions/${id}`).then((r) => r.data);
export const getSessionStatus = (id: string) => api.get(`/api/sessions/${id}/status`).then((r) => r.data);
export const deleteSession = (id: string) => api.delete(`/api/sessions/${id}`).then((r) => r.data);
export const updateSession = (id: string, data: { name?: string; description?: string; folder_id?: string }) =>
  api.patch(`/api/sessions/${id}`, null, { params: data }).then((r) => r.data);
export const getSessionTree = (id: string) => api.get(`/api/sessions/${id}/tree`).then((r) => r.data);

// Upload
export const uploadVideo = (formData: FormData) =>
  api.post("/api/upload", formData).then((r) => r.data);
// NOTE: Do NOT set Content-Type manually for FormData.
// The browser must set it automatically as:
//   "multipart/form-data; boundary=----WebKitFormBoundaryXYZ..."
// Setting it manually breaks the boundary and the server can't parse the file.

// Steps
export const getSteps = (sessionId: string) => api.get(`/api/sessions/${sessionId}/steps`).then((r) => r.data);
export const getStep = (stepId: string) => api.get(`/api/steps/${stepId}`).then((r) => r.data);

// Chat
export const sendChat = (sessionId: string, message: string) =>
  api.post(`/api/sessions/${sessionId}/chat`, { message }).then((r) => r.data);
export const getChatHistory = (sessionId: string) =>
  api.get(`/api/sessions/${sessionId}/chat/history`).then((r) => r.data);
export const clearChatHistory = (sessionId: string) =>
  api.delete(`/api/sessions/${sessionId}/chat/history`).then((r) => r.data);

// Search
export const search = (q: string, sessionId?: string) =>
  api.get("/api/search", { params: { q, session_id: sessionId } }).then((r) => r.data);

// Annotations
export const getAnnotations = (stepId: string) => api.get(`/api/steps/${stepId}/annotations`).then((r) => r.data);
export const addAnnotation = (stepId: string, data: { author_name: string; content: string }) =>
  api.post(`/api/steps/${stepId}/annotations`, data).then((r) => r.data);
export const deleteAnnotation = (annotationId: string) => api.delete(`/api/annotations/${annotationId}`).then((r) => r.data);

// Bookmarks
export const getBookmarks = (sessionId: string) => api.get(`/api/sessions/${sessionId}/bookmarks`).then((r) => r.data);
export const addBookmark = (data: { step_id: string; session_id: string; label: string }) =>
  api.post("/api/bookmarks", data).then((r) => r.data);
export const deleteBookmark = (bookmarkId: string) => api.delete(`/api/bookmarks/${bookmarkId}`).then((r) => r.data);

// Tags
export const getTags = () => api.get("/api/tags").then((r) => r.data);
export const createTag = (data: { name: string; color: string }) => api.post("/api/tags", data).then((r) => r.data);
export const assignTag = (sessionId: string, tagId: string) =>
  api.post(`/api/sessions/${sessionId}/tags`, { tag_id: tagId }).then((r) => r.data);
export const removeTag = (sessionId: string, tagId: string) =>
  api.delete(`/api/sessions/${sessionId}/tags/${tagId}`).then((r) => r.data);

// Folders
export const getFolders = () => api.get("/api/folders").then((r) => r.data);
export const createFolder = (data: { name: string; color: string }) => api.post("/api/folders", data).then((r) => r.data);
export const deleteFolder = (id: string) => api.delete(`/api/folders/${id}`).then((r) => r.data);
export const updateFolder = (id: string, data: { name?: string; color?: string }) =>
  api.patch(`/api/folders/${id}`, data).then((r) => r.data);

// Compare
export const compareSessions = (idA: string, idB: string) =>
  api.post("/api/compare", { session_id_a: idA, session_id_b: idB }).then((r) => r.data);

// Export
export const exportSession = (sessionId: string, params: Record<string, any>) =>
  api.get(`/api/sessions/${sessionId}/export`, { params, responseType: "blob" }).then((r) => r.data);
export const generateSOP = (sessionId: string) =>
  api.post(`/api/sessions/${sessionId}/sop`).then((r) => r.data);

export default api;
