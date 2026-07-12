document.addEventListener('DOMContentLoaded', () => {
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = document.body.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      document.body.setAttribute('data-theme', current);
      document.documentElement.setAttribute('data-bs-theme', current);
    });
  }

  const analysisForm = document.getElementById('analysisForm');
  if (analysisForm) {
    analysisForm.addEventListener('submit', (event) => {
      const resumeText = document.getElementById('resume_text').value.trim();
      const resumeFile = document.getElementById('resume_file').files.length;
      const jobDescription = document.getElementById('job_description').value.trim();

      if (!jobDescription) {
        event.preventDefault();
        alert('Job description is required.');
        return;
      }

      if (!resumeText && resumeFile === 0) {
        event.preventDefault();
        alert('Please paste resume text or upload a PDF/DOCX resume.');
      }
    });
  }
});
