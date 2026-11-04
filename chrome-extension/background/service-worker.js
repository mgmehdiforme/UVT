// UVT Background Service Worker (Manifest V3)

// Enables Chrome Side Panel on action click
chrome.sidePanel
  .setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error("Error setting side panel behavior:", error));

chrome.runtime.onInstalled.addListener(() => {
  console.log("UVT Extension installed successfully.");
});
