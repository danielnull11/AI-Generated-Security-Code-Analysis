# AI-Generated Code Security Analysis

**Independent project · In progress**

## Why I started this

I started this project to see what security issues I could identify in an AI generated web app, then learn how to fix and test them before deployment.
A lot of people are using coding agents to build websites and applications incredibly fast, but nobody talks about the security risks and how to secure them before publishing them. 

## What I built

I generated a functional photography portfolio application using Python and FastAPI. It includes a photo gallery, admin login, image uploads, camera metadata extraction, and a SQLite database.

## What I've tested so far

I reviewed the backend for common security issues and focused my first tests on two areas:

- **File uploads:** The code checks file extensions without validating the actual image contents. In local testing, I was able to upload non-image content with a `.jpg` extension.
- **Image metadata:** The application saves EXIF metadata without sanitizing it. I tested injecting script-like text into metadata and inspecting what was stored in SQLite. **This is not proof of stored XSS executing in a browser**; the existing Jinja2 templates escape HTML output.

I also noticed configuration issues involving JWT secrets and Docker privileges that I want to address.

The original test payloads are not preserved in the current project snapshot. I'll add reproducible evidence as I repeat the tests.

## What I'm working on next

- Validate uploaded files by their actual image contents and limit upload size.
- Handle untrusted EXIF metadata safely and verify the resulting HTML output.
- Improve JWT configuration and run the Docker container as a non-root user.
- Repeat the original tests and document what changed, with screenshots and code comparisons.

## Project status

**The application and initial security review are complete. Security fixes and retesting are still in progress.** This is a learning project, not a production-ready application or a formal penetration test.

## Tech used

Python · FastAPI · SQLite · SQLAlchemy · Jinja2 · Pillow · Docker · ExifTool

---

*This README is a starting point. I'll replace the project motivation and testing notes with my own explanation and evidence as I continue.*
