Resource Sharing Platform

Overview

This project is a cloud-based platform designed to facilitate efficient resource sharing using the capabilities of AWS and Azure services. The platform provides tools to summarize YouTube videos and generate tags from PDF files, enabling streamlined sharing and utilization of resources.

Features

YouTube AI Summarizer:

Generates AI-powered summaries for YouTube videos by entering a URL.

Displays a video preview alongside the summary.

PDF Tag Generator:

Automatically generates relevant tags from uploaded PDF files.

Provides a user-friendly interface to upload PDFs and view the generated tags.

Technologies Used

AWS Services

Amazon S3: Used for storage of shared resources and files.

Amazon Bedrock: Utilized for AI-based summarization.

Amazon Transcribe: Employed for converting video audio into text for processing.

Azure Services

Azure SQL Database: Used for managing and storing structured resource data efficiently.

Prerequisites

AWS and Azure accounts with access to the respective services.

Proper API keys and credentials for accessing the services.

A modern web browser for accessing the application.

How It Works

YouTube Summarization:

The user inputs a YouTube video URL.

The application fetches the video, transcribes its audio using Amazon Transcribe, and processes the transcript with Amazon Bedrock to generate a concise summary.

A video preview is displayed for user convenience.

PDF Tag Generation:

The user uploads a PDF file.

The application analyzes the content and generates contextually relevant tags using advanced AI models.

Setup and Installation

Clone the repository to your local machine:

git clone <repository-url>

Configure AWS and Azure credentials in the application settings.

Install necessary dependencies by running:

npm install

Start the application:

npm start

Access the application in your browser at http://localhost:3000.

Project Workflow

Upload or input data (YouTube URL or PDF file).

Process the data through AWS and Azure services.

Display results (summary or tags) in a user-friendly interface.

Screenshot

Below is a screenshot of the application interface:



Future Enhancements

Support for additional cloud services and features.

Advanced customization options for generated summaries and tags.

Enhanced mechanisms for resource sharing and collaboration.

License

This project is licensed under the MIT License.

