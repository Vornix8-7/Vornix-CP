# Vornix CP
### Your Personal Competitive Programming Coach

**Video Demo:** https://youtu.be/RSUuj75mnB4

**Author:** Azizbek Valijonov
**GitHub Username:** Vornix8-7
**Course:** CS50x – Introduction to Computer Science

---

## About the Project

Vornix CP is a web application I created to make competitive programming practice more organized and effective. The main idea came from a problem that many competitive programmers face: it is not always easy to keep track of solved problems, understand personal weaknesses, and decide what to practice next.

When preparing for programming contests, solving problems is important, but simply solving random tasks does not always lead to improvement. It is also necessary to understand which topics are difficult, follow progress over time, and practice problems at an appropriate difficulty level.

I wanted to bring these activities together in one application instead of having to use different websites, spreadsheets, and personal notes.

That is why I developed Vornix CP. It is designed not only as a problem tracker but also as a personal competitive programming coach. Users can connect their Codeforces accounts, view their rating information, organize problems, analyze submissions, and discover new practice opportunities.

I chose a dark interface with a sidebar navigation system because I wanted the application to look clean and professional while keeping its main features easy to access.

## Main Features

### 1. User Registration and Login

The application has a registration and login system. Users can create their own accounts and access their personal information.

Each account has its own data, so users can manage their problems and training information separately. Passwords are stored as password hashes instead of being saved as plain text.

### 2. Dashboard

The dashboard gives users a quick overview of their competitive programming progress.

It displays important information, including:

- Current Codeforces rating.
- Maximum Codeforces rating.
- Target rating.
- Number of solved problems in the personal collection.
- Problems that are still in progress.
- Rating history.

I wanted the dashboard to show the most important information immediately after logging in. It also provides shortcuts to other sections, so users do not have to search through different pages to find what they need.

The rating history is displayed using a line chart, which makes changes in performance easier to understand.

### 3. Codeforces Account Integration

One of the features I wanted to include from the beginning was Codeforces integration.

Users can connect their Codeforces handle to the application. Vornix CP then uses the Codeforces API to retrieve publicly available information about their account and submissions.

This includes information such as current rating, maximum rating, contest history, submitted problems, problem ratings, tags, and submission verdicts.

I chose Codeforces because it is one of the platforms I wanted the application to support, and its API makes it possible to work with real competitive programming data.

Instead of asking users to enter every detail manually, the application can retrieve much of this information automatically.

### 4. Problem Management

Keeping track of practice problems can become difficult, especially when working on several topics at the same time.

The problem management section allows users to create their own problem collection and organize tasks according to their difficulty, platform, and solving status.

Problems can be marked as:

- To Do
- In Progress
- Solved

Users can also keep notes about their problems.

I included this feature because I wanted a simple way to remember which problems I planned to solve and which ones I had already completed.

### 5. Problem Finder

The Problem Finder helps users discover Codeforces problems.

Users can explore problems using information such as problem names and ratings. This makes it easier to find tasks that match their current level.

I wanted this section to make the process of finding practice problems quicker and more convenient.

### 6. Training Coach and Topic Analysis

The Training Coach is one of the most important parts of Vornix CP.

I wanted the application to do more than store information. It should also help users understand their performance.

The Training Coach analyzes Codeforces submissions and groups attempted problems by their tags. It then compares accepted submissions with attempted problems to estimate performance in different topics.

For example, a user might perform well in greedy problems but have more difficulty with dynamic programming or graphs. Seeing this information can help them decide where to focus their practice.

The analysis includes:

- Topics with relatively strong results.
- Topics that may need more attention.
- Number of attempted problems.
- Number of accepted problems.
- Estimated success percentages.
- Recommended problems related to weaker topics.

The recommended problems are also selected with the user's current rating in mind. This helps users find tasks that are closer to their current skill level.

These results are estimates based on available submission data. They are intended to guide practice rather than provide a perfect measurement of someone's programming ability.

### 7. Virtual Contest Recommendations

Another feature I wanted to add was virtual contest practice.

Codeforces has many previous contests that are useful for additional training. However, choosing a suitable contest is not always easy.

Vornix CP retrieves finished contests and estimates their difficulty using the average rating of their rated problems. It then compares this estimate with the user's current rating.

Users can browse recommended contests and start tracking a virtual contest. The application also provides a link to open the original contest on Codeforces.

After finishing a tracked attempt, Vornix CP checks the user's submissions and counts accepted problems submitted after the tracking session started.

This gives users a basic record of their virtual contest practice and helps them keep track of their results.

## Technologies Used

I used several technologies to build this application:

- **Python:** Used for the main application logic and backend functionality.
- **Flask:** Used to create the web application, handle routes, and manage user sessions.
- **SQLite:** Used to store user accounts, problems, submissions, and other application data.
- **HTML:** Used to build the structure of the web pages.
- **CSS:** Used to design the interface, including the dark theme, sidebar, cards, and layouts.
- **JavaScript:** Used for interactive features in the browser.
- **Chart.js:** Used to display rating history as a line chart.
- **Codeforces API:** Used to retrieve Codeforces profile, contest, and submission information.

I selected these technologies because they work well together and allowed me to build the application using tools that I could understand, test, and improve.

## Database Design

I used SQLite as the database because it is lightweight and works well for a Flask application.

The database is divided into several tables, each responsible for storing a different type of information.

The `users` table stores account information, including usernames, email addresses, password hashes, and Codeforces profile details.

The `problems` table stores the problems users add to their collections. It contains information such as titles, platforms, difficulty, links, notes, and solving status.

The `tags` and `problem_tags` tables are used to organize problems by programming topics.

Other tables store problem attempts, personal goals, study sessions, and rating history.

I also added tables for the Training Coach and virtual contests. The `cf_submissions` table stores synchronized Codeforces submission data, while `coach_sync` records when the last synchronization happened. The `virtual_contests` table stores information about tracked contest attempts.

I separated the data into different tables to make the database easier to understand and maintain.

## Project Files

The main files and folders have the following responsibilities:

- `app.py` – Starts and configures the Flask application.
- `config.py` – Stores application configuration.
- `database.py` – Handles database connections, initialization, and migrations.
- `helpers.py` – Contains reusable functions, including Codeforces API requests.
- `schema.sql` – Defines the initial database structure.
- `routes/` – Contains the backend routes for the different application pages.
- `templates/` – Contains the HTML templates rendered by Flask.
- `static/css/` – Contains the CSS used to style the application.
- `instance/` – Stores the local SQLite database.

I kept the project separated into different files so that individual parts could be updated without having to rewrite the entire application.

## How to Run

To run Vornix CP locally, Python and Flask must be installed.

First, open the project directory:

```bash
cd project
```

Install Flask:

```bash
pip install Flask
```

Initialize the database if it has not already been initialized:

```bash
python -c "from app import app; from database import init_db; app.app_context().push(); init_db()"
```

Then start the application:

```bash
python app.py
```

Open the local address displayed in the terminal. Usually, it is:

```text
http://127.0.0.1:5000
```

After opening the application, users can register, log in, and connect their Codeforces accounts.

An internet connection is needed for features that communicate with the Codeforces API.

## Challenges and What I Learned

Building Vornix CP helped me understand how different parts of a web application work together.

One challenge was connecting the Flask backend to the SQLite database and making sure that information was stored correctly for each user.

Another challenge was working with an external API. I had to understand how to send requests, receive responses, and use the returned information in my application.

I also learned more about organizing a Flask project using routes, templates, helper functions, and database migrations.

Working on the dashboard and rating chart helped me understand how backend data can be displayed in a more visual and useful way.

Most importantly, this project gave me experience turning an idea into a working application and improving it through testing and debugging.

## Future Improvements

There are still many things I would like to add to Vornix CP.

Some ideas include more advanced topic analysis, better problem recommendations, automatic daily training plans, detailed virtual contest reports, penalty calculations, and support for additional competitive programming platforms.

I would also like to improve the statistics section and give users more ways to understand their progress over longer periods.

These improvements could make Vornix CP an even more useful tool for competitive programmers.

## AI Acknowledgement

AI tools were used as development assistance during parts of this project. I used this assistance for debugging, understanding errors, reviewing code, and improving certain parts of the implementation.

I remain responsible for the project's design decisions, testing, development process, and final implementation.

---

## Final Thoughts

Vornix CP started with a simple idea: make competitive programming practice easier to organize and understand.

During development, it grew into a web application that combines problem management, Codeforces integration, rating tracking, topic analysis, and virtual contest practice.

I hope to continue improving it and eventually turn it into a more complete training platform.

**VornixCP — Practice smarter. Analyze better. Improve consistently.**
