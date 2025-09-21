#!/usr/bin/env python3
import os
from nanda_adapter import NANDA
from crewai import Agent, Task, Crew
from langchain_anthropic import ChatAnthropic

def create_sarcastic_improvement():
    """Create a CrewAI-powered sarcastic improvement function"""
    
    # Initialize the LLM
    llm = ChatAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-haiku-20240307"
    )
    
    # Create a sarcastic agent
    sarcastic_agent = Agent(
        role="Sarcastic Message Transformer",
        goal="Transform messages into witty, sarcastic responses while maintaining the core meaning",
        backstory="""You are a master of sarcasm and wit. You excel at taking ordinary messages 
        and transforming them into clever, sarcastic versions that are humorous but not mean-spirited. 
        You use techniques like irony, exaggeration, and dry humor to make messages more entertaining.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    def sarcastic_improvement(message_text: str) -> str:
        """Transform message to sarcastic version"""
        try:
            # Create a task for the sarcastic transformation
            sarcastic_task = Task(
                description=f"""Transform the following message into a sarcastic, witty version.
                Use sarcasm, irony, and dry humor while keeping the core meaning intact.
                Make it entertaining but not offensive or mean-spirited.
                
                Original message: {message_text}
                
                Provide only the sarcastic transformation, no explanations.""",
                expected_output="A sarcastic, witty version of the original message",
                agent=sarcastic_agent
            )
            
            # Create and run the crew
            crew = Crew(
                agents=[sarcastic_agent],
                tasks=[sarcastic_task],
                verbose=True
            )
            
            result = crew.kickoff()
            return str(result).strip()
            
        except Exception as e:
            print(f"Error in sarcastic improvement: {e}")
            return f"Oh wow, {message_text}. How absolutely groundbreaking."  # Fallback sarcastic transformation
    
    return sarcastic_improvement

def main():
    """Main function to start the sarcastic agent"""
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Please set your ANTHROPIC_API_KEY environment variable")
        return
    
    # Create sarcastic improvement function
    sarcastic_logic = create_sarcastic_improvement()
    
    # Initialize NANDA with sarcastic logic
    nanda = NANDA(sarcastic_logic)
    
    # Start the server
    print("Starting Sarcastic Agent with CrewAI...")
    print("All messages will be transformed to sarcastic responses!")
    
    domain = os.getenv("DOMAIN_NAME", "localhost")
    
    if domain != "localhost":
        # Production with SSL
        nanda.start_server_api(os.getenv("ANTHROPIC_API_KEY"), domain)
    else:
        # Development server
        nanda.start_server()

if __name__ == "__main__":
    main()