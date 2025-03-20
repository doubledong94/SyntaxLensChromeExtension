chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "sendText",
    title: "发送文字到本地服务",
    contexts: ["selection"],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "sendText") {
    chrome.tabs.sendMessage(tab.id, { text: info.selectionText });
  }
});

function sendTextToService(selectedText) {
  // 这里将selectedText传递给content.js
  chrome.runtime.sendMessage({text: selectedText});
}