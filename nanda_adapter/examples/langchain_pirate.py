#!/usr/bin/env python3
import os
from nanda_adapter import NANDA
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic

def create_pirate_improvement():
    """Create a LangChain-powered pirate improvement function"""

    # Initialize the LLM
    llm = ChatAnthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-haiku-20240307"
    )

    # Create a prompt template for pirate transformation
    prompt = PromptTemplate(
        input_variables=["message"],
        template="""Transform the following message into pirate 
English. 
        Use pirate vocabulary, grammar, and expressions like 'ahoy', 
'matey', 'ye', 'arrr', etc.
        Keep the core meaning intact but make it sound like a pirate 
would say it.
        
        Original message: {message}
        
        Pirate version:"""
    )

    # Create the chain
    chain = prompt | llm | StrOutputParser()

    def pirate_improvement(message_text: str) -> str:
        """Transform message to pirate English"""
        try:
            result = chain.invoke({"message": message_text})
            return result.strip()
        except Exception as e:
            print(f"Error in pirate improvement: {e}")
            return f"Arrr! {message_text}, matey!"  # Fallback pirate transformation

    return pirate_improvement

def main():
    """Main function to start the pirate agent"""

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Please set your ANTHROPIC_API_KEY environment variable")
        return

    # Create pirate improvement function
    pirate_logic = create_pirate_improvement()

    # Initialize NANDA with pirate logic
    nanda = NANDA(pirate_logic)

    # Start the server
    print("Starting Pirate Agent with LangChain...")
    print("All messages will be transformed to pirate English!")

    domain = os.getenv("DOMAIN_NAME", "localhost")

    if domain != "localhost":
        # Production with SSL
        nanda.start_server_api(os.getenv("ANTHROPIC_API_KEY"), domain)
    else:
        # Development server
        nanda.start_server()

if __name__ == "__main__":
    main()