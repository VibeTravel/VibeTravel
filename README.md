## Vibe_Travel.
An agentic AI approach to finding and planning travels.

Most of the code at this point is in agents folder inside location finder. 

3 agents have been created until now.

    - The first agent takes the input from the user to know the user preference.
    - The second agent searches the web for the most suitable travel options to suggest the user.
    - The third agent displays the searched options to get a rating for each travel proposal from the user.
    - The outputs of the third agent are stored in either of preferred_destinations or unpreferred_destinations. preferred_destinations will be used in the very next part for detailed information generation whereas the unpreferred_destinations can be used later on for customizing user preference.

The next steps are as follows:
1. Implement an agent(Detail_Information_agent) that takes in the data stored in preferred_destinations to research about the destinations in depth. This includes searching for flights and bookings and other necessary details.
2. Implement an agent that generates the complete itinerary from the information gathered by the previous agent(Detail_Information_agent).
3. Display the final results in a neat and clean format.

The other steps:
1. Implement memory and state.
2. Implement front-end and backends using a web app and remove certain agents(like trip_input_agent and destination_rater_agent).
3. Implement robust communication between adk framework and backend. 
4. Implement a cloud based Database(most likely VertexAI) for storing user information and session information.
5. Implement Some form of Reinforcement Learning/ Recommender System using User Data.

## To run the code:
1. Clone the repo
2. Create a `.env` file inside agents folder and add GEMINI_API_KEY or GOOGLE_API_KEY.
3. Use terminal to get to the parent folder of agents folder.
4. Run `adk web` in the terminal.
5. Click on the link that is shown in the terminal which redirects you to a new website.
6. From the top left side, select agents and start chatting with the chatbot. 