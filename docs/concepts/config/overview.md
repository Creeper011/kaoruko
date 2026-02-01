# Configuration System Overview

This system can be finded in: src/infrastructure/services/config

The configuration system is a crucial part of the project's operation. Without it, we would not be able to easily change or maintain important information that contributes to the execution and functioning of the code.

- The concept revolves almost entirely around the configuration model, `ApplicationSettings`, an immutable dataclass that contains all settings (including infrastructure details) related to the application and its operation.

- The configuration system is divided into 4 categories with their respective roles:  
    - **Factory** → Coordinates the entire process to build the configuration model  
    - **Loaders** → Only load configuration data  
    - **Parsers** → Convert received data into objects  
    - **Mappers** → Map and build the configuration model

- Furthermore, the Factory does not directly depend on any dependencies; it expects them to be injected, which facilitates testing and mocking.  
    - Note: It is important to highlight that the Factory expects an implementation/interface of a Config loader, which is a key factor to ensure testability and mockability.

- As mentioned before, this implementation ensures excellent testability by following modern software engineering principles.

- NOTE: Loaders and Mappers are organized into dedicated modules (one folder per responsibility) and are dynamically discovered and injected through `LoadersFinders` and `MappersFinders`, further reducing coupling and improving extensibility.