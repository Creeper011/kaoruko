# Architecture Concept

NOTE: (Current state of the project): 
At the beginning, the project was intended to follow a very strict and robust Clean Architecture approach. However, my philosophy has changed over time, and I am currently refactoring parts of the architecture to make it more modular while still being inspired by Clean Architecture principles.

## Current architecture:

- ## Layers:
    - Application  
      Defines how command flows should occur within the application.

    - Bootstrap  
      Acts as the Composition Root. It is composed of multiple separated modules organized through a builder system, where builders are responsible for constructing components and compositors are responsible for wiring things together (e.g., establishing connections).

    - Infrastructure  
      Contains all external implementations used by the application, allowing fast and flexible replacement of modules.

    - Domain  
      Defines core application rules without depending on external implementations.

    - Presentation  
      Contains everything that is presented to the user.

    - Core  
      Currently defines shared constants used across the codebase.

    - Utils  
      Defines utility helpers that are not required at runtime.

    NOTE: The use of pathlib.Path inside the Domain layer is intentional, in order to guarantee compatibility.

## Flow:
main.py -> ApplicationBuilder -> Builders / Compositors -> Application Model (executed by main.py)
