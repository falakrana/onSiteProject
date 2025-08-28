"""
Natural Language to Database Schema Generator Demo
Uses LangChain with Google Gemini AI to convert business requirements to normalized DB schemas
"""

import re
import os
import json
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from langchain.schema.runnable import RunnableSequence, RunnablePassthrough

@dataclass
class Field:
    name: str
    data_type: str
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = None
    constraints: List[str] = None

    def __post_init__(self):
        if self.constraints is None:
            self.constraints = []

@dataclass
class Table:
    name: str
    fields: List[Field]
    primary_key: str
    foreign_keys: List[Dict[str, str]]
    description: str = ""

@dataclass
class Relationship:
    from_table: str
    to_table: str
    relationship_type: str
    explanation: str

class SchemaGenerator:
    def __init__(self, google_api_key: str = None):
        """Initialize the schema generator with Google API key"""
        if google_api_key:
            os.environ["GOOGLE_API_KEY"] = google_api_key
        elif not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("Please provide Google API key or set GOOGLE_API_KEY environment variable")
        
        # Initialize Google Gemini AI through LangChain
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            max_tokens=2048
        )
        
        self.schema_prompt = self._create_schema_prompt()
        self.query_prompt = self._create_query_prompt()
        self.optimization_prompt = self._create_optimization_prompt()
        
    def _create_schema_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for schema generation"""
        system_message = """You are a senior database architect with expertise in relational database design and normalization. 
        Your task is to convert business requirements into well-normalized relational database schemas."""
        
        human_template = """
        Business Requirement: {requirement}

        Please design a normalized relational database schema following these guidelines:
        1. Follow 3NF (Third Normal Form) principles
        2. Use appropriate data types for each field
        3. Define primary keys and foreign keys correctly
        4. Create proper relationships between tables
        5. Use meaningful table and column names

        Provide your response in the following JSON format:
        {{
            "tables": [
                {{
                    "name": "table_name",
                    "description": "Brief description of what this table stores",
                    "fields": [
                        {{
                            "name": "field_name",
                            "data_type": "VARCHAR(100) | INT | DATE | etc.",
                            "is_primary_key": true/false,
                            "is_foreign_key": true/false,
                            "references": "referenced_table.field_name (if foreign key)",
                            "constraints": ["NOT NULL", "UNIQUE", etc.]
                        }}
                    ]
                }}
            ],
            "relationships": [
                {{
                    "from_table": "table1",
                    "to_table": "table2",
                    "relationship_type": "one-to-many | many-to-one | many-to-many",
                    "explanation": "Why this relationship exists"
                }}
            ],
            "design_decisions": [
                "Explanation for each major design decision"
            ]
        }}
        """
        
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            HumanMessage(content=human_template)
        ])
    
    def _create_query_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for SQL query generation"""
        system_message = """You are a SQL expert. Generate practical, well-commented SQL queries 
        that demonstrate how to use the provided database schema effectively."""
        
        human_template = """
        Given this database schema:
        {schema_json}
        
        Generate 3-4 example SQL queries with the following types:
        1. INSERT queries to add realistic sample data (at least 2-3 records per table)
        2. SELECT query with JOINs to retrieve related data
        3. UPDATE query to modify existing data
        4. DELETE query (optional, with proper constraints)
        
        Make the queries realistic for the business domain and include comments explaining what each query does.
        Format as:
        
        -- Query 1: Insert sample data
        INSERT INTO table_name (field1, field2) VALUES (value1, value2);
        
        -- Query 2: Retrieve related data
        SELECT ... FROM ... JOIN ... WHERE ...;
        
        etc.
        """
        
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            HumanMessage(content=human_template)
        ])
    
    def _create_optimization_prompt(self) -> ChatPromptTemplate:
        """Create prompt template for optimization suggestions"""
        system_message = """You are a database performance expert. Analyze database schemas 
        and provide optimization recommendations."""
        
        human_template = """
        Database Schema: {schema_json}
        
        Provide optimization suggestions including:
        1. Recommended indexes for better query performance
        2. Potential normalization improvements
        3. Suggestions for handling large datasets
        4. Security considerations
        
        Format as a bulleted list with explanations.
        """
        
        return ChatPromptTemplate.from_messages([
            SystemMessage(content=system_message),
            HumanMessage(content=human_template)
        ])

    def generate_schema(self, requirement: str) -> Dict:
        """Generate database schema from natural language requirement"""
        try:
            # Create chain and generate schema
            schema_chain = self.schema_prompt | self.llm
            response = schema_chain.invoke({"requirement": requirement})
            
            # Parse JSON response
            schema_data = self._parse_schema_response(response)
            
            return {
                'tables': schema_data.get('tables', []),
                'relationships': schema_data.get('relationships', []),
                'design_decisions': schema_data.get('design_decisions', []),
                'raw_response': response,
                'parsed_successfully': True
            }
            
        except Exception as e:
            print(f"Error generating schema: {e}")
            return {
                'tables': [],
                'relationships': [],
                'design_decisions': [f"Error parsing response: {e}"],
                'raw_response': response if 'response' in locals() else "",
                'parsed_successfully': False
            }
    
    def generate_queries(self, schema_data: Dict) -> str:
        """Generate example SQL queries for the schema"""
        try:
            schema_json = json.dumps(schema_data, indent=2)
            query_chain = self.query_prompt | self.llm
            return query_chain.invoke({"schema_json": schema_json})
        except Exception as e:
            return f"Error generating queries: {e}"
    
    def generate_optimizations(self, schema_data: Dict) -> str:
        """Generate optimization suggestions for the schema"""
        try:
            schema_json = json.dumps(schema_data, indent=2)
            opt_chain = self.optimization_prompt | self.llm
            return opt_chain.invoke({"schema_json": schema_json})
        except Exception as e:
            return f"Error generating optimizations: {e}"
    
    def _parse_schema_response(self, response: str) -> Dict:
        """Parse JSON response from LLM"""
        try:
            # Extract JSON from response (in case there's extra text)
            response_content = response.content if hasattr(response, 'content') else response
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_str = response_content[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: try to parse entire response as JSON
                return json.loads(response_content)
                
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            # Fallback to simple text parsing
            return self._fallback_parse(response)
    
    def _fallback_parse(self, response: str) -> Dict:
        """Fallback parsing when JSON parsing fails"""
        return {
            'tables': [{'name': 'parsing_error', 'description': 'Could not parse response', 'fields': []}],
            'relationships': [],
            'design_decisions': ['Response parsing failed - please check the raw response']
        }

class SchemaValidator:
    """Validate generated schemas for common issues"""
    
    @staticmethod
    def validate_schema(schema_data: Dict) -> List[str]:
        """Validate schema and return list of issues"""
        issues = []
        
        tables = schema_data.get('tables', [])
        if not tables:
            issues.append("No tables found in schema")
            return issues
        
        table_names = [table['name'] for table in tables]
        
        for table in tables:
            # Check if table has primary key
            has_pk = any(field.get('is_primary_key', False) for field in table.get('fields', []))
            if not has_pk:
                issues.append(f"Table '{table['name']}' has no primary key")
            
            # Check for foreign key references
            for field in table.get('fields', []):
                if field.get('is_foreign_key', False):
                    ref = field.get('references', '')
                    if ref and '.' in ref:
                        ref_table = ref.split('.')[0]
                        if ref_table not in table_names:
                            issues.append(f"Foreign key in '{table['name']}.{field['name']}' references non-existent table '{ref_table}'")
        
        return issues

def print_schema_results(requirement: str, schema_data: Dict, queries: str, optimizations: str = None):
    """Print formatted schema results"""
    print("=" * 100)
    print(f"🎯 BUSINESS REQUIREMENT: {requirement}")
    print("=" * 100)
    
    if not schema_data.get('parsed_successfully', False):
        print("❌ SCHEMA GENERATION FAILED")
        print("Raw Response:")
        print(schema_data.get('raw_response', 'No response'))
        return
    
    # Print tables
    print("\n📋 GENERATED DATABASE SCHEMA:")
    print("-" * 60)
    
    for table in schema_data.get('tables', []):
        print(f"\n🗂️  Table: {table['name'].upper()}")
        if table.get('description'):
            print(f"   Description: {table['description']}")
        
        for field in table.get('fields', []):
            field_desc = f"   • {field['name']} ({field['data_type']})"
            
            if field.get('is_primary_key'):
                field_desc += " [PRIMARY KEY]"
            if field.get('is_foreign_key') and field.get('references'):
                field_desc += f" [FK → {field['references']}]"
            if field.get('constraints'):
                field_desc += f" [{', '.join(field['constraints'])}]"
                
            print(field_desc)
    
    # Print relationships
    relationships = schema_data.get('relationships', [])
    if relationships:
        print("\n🔗 TABLE RELATIONSHIPS:")
        print("-" * 60)
        for rel in relationships:
            print(f"   • {rel['from_table']} → {rel['to_table']} ({rel['relationship_type']})")
            print(f"     {rel['explanation']}")
    
    # Print design decisions
    decisions = schema_data.get('design_decisions', [])
    if decisions:
        print("\n💡 DESIGN DECISIONS:")
        print("-" * 60)
        for i, decision in enumerate(decisions, 1):
            print(f"   {i}. {decision}")
    
    # Validate schema
    validator = SchemaValidator()
    issues = validator.validate_schema(schema_data)
    if issues:
        print("\n⚠️  VALIDATION ISSUES:")
        print("-" * 60)
        for issue in issues:
            print(f"   • {issue}")
    
    # Print example queries
    print("\n📝 EXAMPLE SQL QUERIES:")
    print("-" * 60)
    print(queries)
    
    # Print optimizations if provided
    if optimizations:
        print("\n🚀 OPTIMIZATION SUGGESTIONS:")
        print("-" * 60)
        print(optimizations)

def run_demo():
    """Run the complete demo with example requirements"""
    
    # Example business requirements
    demo_requirements = [
        "Track patients, doctors, and medical appointments with patient history",
        "Manage a library system with books, members, authors, and borrowing records",
        "Handle e-commerce orders with customers, products, inventory, and shipping",
        "Track employees, departments, projects, and work assignments",
        "Manage university courses, students, professors, and enrollments"
    ]
    
    print("🏥 Natural Language to Database Schema Generator")
    print("   Powered by Google Gemini AI via LangChain")
    print("=" * 100)
    
    try:
        # Initialize generator (you need to set GOOGLE_API_KEY environment variable)
        generator = SchemaGenerator()
        
        print("Available demo requirements:")
        for i, req in enumerate(demo_requirements, 1):
            print(f"   {i}. {req}")
        
        choice = input(f"\nSelect a requirement (1-{len(demo_requirements)}) or press Enter for #1: ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(demo_requirements):
            requirement = demo_requirements[int(choice) - 1]
        else:
            requirement = demo_requirements[0]  # Default to first option
        
        print(f"\n🔄 Processing: {requirement}")
        print("   This may take 15-30 seconds...")
        
        # Generate schema
        schema_data = generator.generate_schema(requirement)
        
        # Generate queries
        queries = generator.generate_queries(schema_data)
        
        # Generate optimization suggestions
        optimizations = generator.generate_optimizations(schema_data)
        
        # Display results
        print_schema_results(requirement, schema_data, queries, optimizations)
        
        # Show extension capabilities
        print("\n" + "=" * 100)
        print("🔧 EXTENSIBILITY FEATURES:")
        print("-" * 60)
        print("✅ Schema Validation - Checks for common database design issues")
        print("✅ Optimization Suggestions - Performance and security recommendations")
        print("✅ Multiple AI Models - Easy to switch between different LLMs")
        print("✅ Custom Prompts - Modifiable templates for different use cases")
        print("✅ JSON Output - Structured data for integration with other tools")
        
        print("\n🎯 POSSIBLE EXTENSIONS:")
        print("-" * 60)
        print("• Migration Script Generation - Auto-generate CREATE TABLE statements")
        print("• Visual Schema Diagrams - Generate ERD diagrams")
        print("• Performance Benchmarking - Simulate query performance")
        print("• Multi-database Support - Generate schemas for PostgreSQL, MySQL, etc.")
        print("• Business Rule Validation - Check against domain-specific constraints")
        print("• API Generation - Auto-generate REST API endpoints from schema")
        
    except Exception as e:
        print(f"\n❌ Error running demo: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure you have set the GOOGLE_API_KEY environment variable")
        print("2. Verify your Google AI API key has proper permissions")
        print("3. Check your internet connection")
        print("4. Ensure all dependencies are installed: pip install -r requirements.txt")

def interactive_mode():
    """Interactive mode for custom requirements"""
    try:
        generator = SchemaGenerator()
        
        print("\n" + "="*60)
        print("🤖 INTERACTIVE MODE - Enter Your Custom Requirement")
        print("="*60)
        
        requirement = input("Describe your business requirement: ").strip()
        
        if not requirement:
            print("No requirement provided. Exiting.")
            return
        
        print(f"\n🔄 Generating schema for: {requirement}")
        print("   Please wait...")
        
        # Generate schema
        schema_data = generator.generate_schema(requirement)
        queries = generator.generate_queries(schema_data)
        optimizations = generator.generate_optimizations(schema_data)
        
        # Display results
        print_schema_results(requirement, schema_data, queries, optimizations)
        
    except Exception as e:
        print(f"Error in interactive mode: {e}")

# Extension classes for future development
class MigrationGenerator:
    """Generate database migration scripts from schema"""
    
    @staticmethod
    def generate_create_statements(schema_data: Dict, db_type: str = "postgresql") -> str:
        """Generate CREATE TABLE statements for the schema"""
        statements = []
        
        for table in schema_data.get('tables', []):
            fields_sql = []
            for field in table.get('fields', []):
                field_sql = f"{field['name']} {field['data_type']}"
                
                if field.get('constraints'):
                    field_sql += " " + " ".join(field['constraints'])
                
                if field.get('is_primary_key'):
                    field_sql += " PRIMARY KEY"
                
                fields_sql.append(field_sql)
            
            # Add foreign key constraints
            fk_constraints = []
            for field in table.get('fields', []):
                if field.get('is_foreign_key') and field.get('references'):
                    fk_constraints.append(
                        f"FOREIGN KEY ({field['name']}) REFERENCES {field['references']}"
                    )
            
            all_constraints = fields_sql + fk_constraints
            
            create_sql = f"CREATE TABLE {table['name']} (\n    " + ",\n    ".join(all_constraints) + "\n);"
            statements.append(create_sql)
        
        return "\n\n".join(statements)

class PerformanceAnalyzer:
    """Analyze and suggest performance improvements"""
    
    @staticmethod
    def suggest_indexes(schema_data: Dict) -> List[str]:
        """Suggest indexes based on schema analysis"""
        suggestions = []
        
        for table in schema_data.get('tables', []):
            table_name = table['name']
            
            # Suggest indexes for foreign keys
            for field in table.get('fields', []):
                if field.get('is_foreign_key'):
                    suggestions.append(f"CREATE INDEX idx_{table_name}_{field['name']} ON {table_name}({field['name']});")
        
        return suggestions

if __name__ == "__main__":
    import sys
    
    print("🚀 Starting Natural Language to Database Schema Generator")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_mode()
    else:
        run_demo()
