var messageHistory = [];
function addMessage(role, content) {
  messageHistory.push({"role": role, "content": content});
}
function getHistory() {
  return messageHistory;
}
document.addEventListener('htmx:afterRequest', function (evt) {
  if (evt.detail.xhr.status != 200 || evt.detail.successful != true) {
    // TODO: handle error in UI
    console.error(evt);
    return;
  }
  if (evt.detail.target.id == 'messages') {
    addMessage('assistant', evt.detail.target.lastElementChild.querySelector("div.hidden").innerText.trim());
  }
});
var textarea = document.getElementById("input");
var heightLimit = 200; /* Maximum height: 200px */

textarea.oninput = function () {
  textarea.style.height = ""; /* Reset the height*/
  textarea.style.height = Math.min(textarea.scrollHeight, heightLimit) + "px";
};

// Return must submit the form unless if shift is also pressed
textarea.onkeydown = function (e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    document.getElementById("btnSubmit").click();
  }
};
