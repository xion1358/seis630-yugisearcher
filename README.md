# Yugisearcher

This project was developed as part of the SEIS 630 Database Mgmt Systems & Design course at the University of St.Thomas  

This web based tool is used to query card data about the YuGiOh! card game.<br/><br/>
This tool sets up a local database and utilizes a server application along with an [api](https://db.ygoresources.com/about/api) to display that information to you.  
At time of development the api contains the latest card data in April 2025 (from what I know).

## Table of Contents

1. [Introduction](#introduction)
2. [Installation Requirements](#installation-requirements)
3. [Installation (Users)](#installation-users)
4. [Installation (Scripts-Devs)](#installation-scripts-devs)
5. [Installation (Docker-Devs)](#installation-docker-devs)
6. [Running Postgres DB](#running-postgres-db)
7. [Usage](#usage)
8. [More Notes and Disclosures](#more-notes-and-disclosures)


## Introduction

The Yugisearcher application can be used to search for cards with text input and retrieve basic information such as the following:
- card id # (Konami official)
- name
- card type
- attack
- defense
- effect
- level/rank/link/pend scale
- ban/limit status

To install the app and run it see the installation steps below. There are many different ways to setup the application.
For users who don't want to bother with the source code, simply run the executable file included. NOTE: Browser required!

For Devs:  
This application utilizes two forms of databases by default.
- By default it uses an embedded database in the form of sqlite.  
- Another form it supports optionally "out-of-the-box" is postgres.  
Find more details below in the Installation sections for Devs.


## Installation Requirements
The directory is should look similar to this under the first yugisearcher directory:  
./yugisearcher  
├── yugisearcher  
├── run.py  
├── requirements.txt  
├── requirements-windows.txt  
├── Readme.md  
├── Dockerfile  
└── docker-compose.yml  

IMPORTANT (mainly for devs, users can skip if only interested in running app): 
- Some of the below directions assume you have a docker client or interface installed. If you don't have one yet, please see [this](https://docs.docker.com/desktop/?_gl=1*k7vvcg*_gcl_au*OTc4OTkzODk1LjE3NDI5MzY0NTE.*_ga*MTgwMzMxMzMxOS4xNzMwODQxNzk1*_ga_XJWPQMJYHQ*MTc0NTM0NDYxMC45LjEuMTc0NTM0NDYxMS41OS4wLjA.).   
    - App was developed with Docker version 28.0.1, build 068a01e.
- You will probably want to have python installed. Please go [here](https://www.python.org/) and install python if you don't already have it installed
    - Tested with Python 3.10, 3.11, and 3.13. Other versions not guarnteed to work but you can give it a try.
- The development environment was with WSL and Windows 11. An attempt was made to mostly make the program os agnostic, but not guaranteed. Best option is to run on a Windows machine if possible.



## Installation (Users)
1. Clone the repository:
    ```bash
    git clone https://github.com/username/project-name.git
    ```

2. Run the executable file at location /yugisearcher/yugisearcher/yugisearcher.exe


3. Go to the server link (by default: http://127.0.0.1:8000/)<br/><br/>
Note: This should open by default, but in the case where it doesn't open then go to it manually 
    - can happen if the computer is taking too long for setting up server

## Installation (Scripts-Devs)

1. Clone the repository:
    ```bash
    git clone https://github.com/xion1358/seis630-yugisearcher.git
    ```

2. Navigate to the yugisearcher/yugisearcher/ directory

3. Use one of the below methods to run/build the application:
 - To run the application (built fresh) simply run the run-dev.py script by doing: 
    ```bash
    python ./run-dev.py
    ```
    NOTE: This will take some time as it'll query the API for some initial data. My testing saw up to 1-2 mins. Yours may be shorter or longer.<br/><br/>
    - You can pass an optional flag to use the postgres database if you have it running (either you set up manually yourself or run the container). Do this with:
        ```bash
        python ./run-dev.py -db=postgres
        ```
 - To build the executable file run: 
    ```bash
    python ./build.py
    ```
    The executable will will be located at /yugisearcher/yugisearcher/yugisearcher.exe

## Installation (Docker-Devs)
This application has support for running both the Postgres DB (or simply rely on the embedded sqlite default if required)  
and the web server all in containers (no need for external installations, aside from docker).<br/>  
You may ask why do this if there are so many ways to launch the application already? 
- It helps when there may be a lot of dependencies that are missing and you simply want to build and run the app fresh in a clean environment.<br/><br/>

To get this running please see the yugisearcher/yugisearcher/docker-compose.yml file. It contains the resources it needs to run the containers, but some are commented out.  
The file goes into it's usage more.<br/><br/>
Once the containers are up you can go to http://127.0.0.1:8000/ to use the application. 

## Running Postgres DB
To run the Postgres DB you can set up your database in a few ways:
- Set up manually according to the settings located at yugisearcher/yugisearcher/settings.py and then run the script:
    ```bash
    python ./run-dev.py -db=postgres
    ```
- Run a docker container. The details to do this is in the docker-compose.yml file but I'll summarize:
  1. Uncomment the code in the docker-compose.yml for the db resource.
  2. Then comment out everything else. This is to ensure you only build and run the top two db and web resources.
  3. Run the command:
        ```bash
        docker-compose up -d db --build
        ```
  4. Wait for the compose to setup fully and then finally run the command:
        ```bash
        python ./run-dev.py -db=postgres
        ```

In addition, you may want a client GUI to work with. I utilized pgAdmin 4. For classmates, its role is similar to SQL Developer.

## Usage
You can search for any text in the Card Name field.  
You can further refine your searches by choosing a Card Type or giving a number to the level, rank, link rating, and pendulum scale.  
Unfortunately due to the API fetch dependency there is a huge bottle neck. The more generic your search is the longer it will take to give you a response.  

Popular and reletively quick searches you can do are as follow:  
  - dark magician
  - blue eyes
  - red eyes
  - exodia  

Other button info:
- Clear the filters with the "Clear Filters" button.  

- Selecting the "Clear Card Data" will clear the database of all the data it has in the card_data table.  
Use this if you are having issues with the database and not getting the results you want (e.g. old data stuck in database).  
Some attempt was made to always be updated with the current card inventory but it wasn't heavily tested.

Seeing duplicates? Nope, due to the way the API handles multiple name translations I have choosen to keep old names when they are changed.  
My guess is that on card release (usually in Japan) the initial translations are given out, but at official English release time they may be given other names.  
The API decided to keep these alternative names with the same card id.  
This leads to some rare different names but same card situation. I decided to retain this so users can search alternative names, but the program inserts the same updated card info even for the older card.    
This leads to a bit of strangeness if someone wants to look at old card definitions, but the API unfortunately doesn't keep this information available (at least not easily retrieved).

## More Notes and Disclosures
Note:
You can connect to this database using the credentials (below is for pgAdmin client, other clients may differ slightly).  
These are the defaults as defined in the docker-compose.yml file.

Host: localhost  
Port: 5432  
Username: searcher  
Password: seis630  
Maintenance Database: yugisearcher  

Disclosure:  
Many scripts and styling were written with the help of LLMs (ChatGPT and Gemini).  
The main search functionality was implemented by Feng Xiong.

This application is a WIP. The software is being developed for educational purposes.

For License please see the LICENSE file included.