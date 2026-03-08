export function renderReplyForm(container) {
  container.innerHTML = `
    <div class="reply-editor">
      <label class="small-title" for="reply-subject-input">Recommended Subject</label>
      <input id="reply-subject-input" class="reply-input" type="text" />
      <label class="small-title" for="reply-body-input">Recommended Reply</label>
      <textarea id="reply-body-input" class="reply-textarea"></textarea>
    </div>
  `;
}

export function setReplyValues(email) {
  const subjectInput = document.getElementById("reply-subject-input");
  const bodyInput = document.getElementById("reply-body-input");
  if (subjectInput) subjectInput.value = email.reply_draft_subject || "";
  if (bodyInput) bodyInput.value = email.reply_draft_body || "";
}

export function getReplyValues() {
  const subjectInput = document.getElementById("reply-subject-input");
  const bodyInput = document.getElementById("reply-body-input");
  return {
    reply_subject: subjectInput ? subjectInput.value : "",
    reply_body: bodyInput ? bodyInput.value : "",
  };
}
