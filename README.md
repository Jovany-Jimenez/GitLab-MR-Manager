# GitLab MR Manager

Hey there! 👋 Welcome to **GitLab MR Manager**! This is your go-to tool for submitting multiple Merge Requests (MRs) in bulk, making it perfect for large organizations that need to implement changes efficiently and stay compliant. Whether you're managing updates across multiple projects or ensuring adherence to organizational policies, this app is here to simplify the process.

## Why Use GitLab MR Manager?

Handling bulk changes can be a daunting task, right? This app provides a streamlined and user-friendly interface to create and manage multiple MRs at once. No more repetitive manual work or worrying about missing something important. It's lightweight, fast, and built with love using Python and Flask.

## How to Get Started

Getting started is super easy! Just follow these steps:

### 1. Clone the Repository
First, grab the code and set it up on your machine:
```bash
git clone <repository-url>
cd GitlabMRManager
```

## Additional Setup: Personal Access Token

To use this tool, you'll need a GitLab Personal Access Token with the proper permissions to create Merge Requests. Follow these steps to generate one:

1. Log in to your GitLab account.
2. Navigate to your profile settings by clicking on your avatar in the top-right corner and selecting **Edit Profile**.
3. In the left-hand menu, go to **Access Tokens**.
4. Give your token a descriptive name (e.g., `BulkMRManager`).
5. Under **Scopes**, select at least the following permissions:
    - `api` (to interact with the GitLab API)
    - `write_repository` (to create Merge Requests)
6. Click **Create personal access token**.
7. Copy the generated token and store it securely. You won't be able to see it again!

### Important Notes:
- Ensure you have the necessary permissions in your GitLab project(s) to create Merge Requests. If you're unsure, contact your GitLab administrator.
- Keep your token private and do not share it with others. Treat it like a password.

Once you have your token, you can configure the app to use it by following the instructions in the app's configuration file or environment variables.
### 2. Set Up a Virtual Environment
It's a good idea to use a Python virtual environment to keep dependencies isolated. Here's how:
```bash
python -m venv .
source /bin/activate  # On Windows, use `venv\Scripts\activate`
```

### 3. Install Dependencies
With the virtual environment activated, install the required packages:
```bash
pip install -r requirements.txt
```

### 4. Run the App
Fire up the app with a single command:
```bash
python app.py
```
Now open your browser and head to `http://localhost:5000`. You're all set!

## How to Use It

- **Bulk MR Creation**: Submit multiple Merge Requests across projects with ease.
- **Stay Compliant**: Ensure organizational changes are applied consistently.
- **Boost Productivity**: Save time and effort with a simple, intuitive interface.

That's it! 🎉 Happy managing, and let us know if you have any feedback or ideas to make this tool even better. 🚀