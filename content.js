chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.text) {
    console.log("Received selected text: " + request.text);
    sendTextToLocalService(request.text);
  }
});

function sendTextToLocalService(selectedText) {
  const formData = new FormData();
  formData.append('text', selectedText);  
  // 发送文字到本地服务
  fetch("http://localhost:3000/parse", { // 假设本地服务运行在3000端口
    method: "POST",
    body: formData
  })
  .then(response => response.blob())
  .then(blob => {
    const imageUrl = URL.createObjectURL(blob);
    displayImage(imageUrl);
  })
  .catch(error => {
    console.error("Error:", error);
  });
}

function displayImage(imageUrl) {
  // 创建图片元素
  const imageContainer = document.createElement("div");
  imageContainer.id = "image-container";
  const image = document.createElement("img");
  image.src = imageUrl;
  const closeButton = document.createElement("button");
  closeButton.id = "close-button";
  closeButton.textContent = "X";

  // 添加事件监听器
  closeButton.addEventListener("click", () => {
    imageContainer.remove();
  });

  // 添加到页面
  imageContainer.appendChild(image);
  imageContainer.appendChild(closeButton);
  document.body.appendChild(imageContainer);

  // 添加拖拽和缩放功能（需要额外的JavaScript库或代码）
  enableDragAndZoom(imageContainer);
}

function enableDragAndZoom(element) {
    let pos1 = 0, pos2 = 0, pos3 = 0, pos4 = 0;
    element.onmousedown = dragMouseDown;

    function dragMouseDown(e) {
        e = e || window.event;
        e.preventDefault();
        pos3 = e.clientX;
        pos4 = e.clientY;
        document.onmouseup = closeDragElement;
        document.onmousemove = elementDrag;
    }

    function elementDrag(e) {
        e = e || window.event;
        e.preventDefault();
        pos1 = pos3 - e.clientX;
        pos2 = pos4 - e.clientY;
        pos3 = e.clientX;
        pos4 = e.clientY;
        element.style.top = (element.offsetTop - pos2) + "px";
        element.style.left = (element.offsetLeft - pos1) + "px";
    }

    function closeDragElement() {
        document.onmouseup = null;
        document.onmousemove = null;
    }
    // 添加缩放功能
    element.addEventListener('wheel', function(e) {
        e.preventDefault();
        const scale = e.deltaY > 0 ? 0.9 : 1.1;
        image.style.transform = `scale(${scale})`;
    })
}