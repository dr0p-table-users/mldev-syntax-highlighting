import os
import ast

def find_classes_with_decorator():
    classes = []
    
    # Get all Python files in current directory
    python_files = [f for f in os.listdir('.') if f.endswith('.py')]
    
    for file_name in python_files:
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                tree = ast.parse(file.read())
                
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class has our decorator
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name) and decorator.func.id == 'experiment_tag':
                                classes.append(node.name)
        except Exception as e:
            print(f"Error processing {file_name}: {e}")
    
    return classes

# Run and save results to Tags.txt
decorated_classes = find_classes_with_decorator()
with open('Tags.txt', 'w', encoding='utf-8') as f:
    if decorated_classes:
        for class_name in decorated_classes:
            f.write(f"{class_name}\n")
    else:
        f.write("No classes with @experiment_tag() decorator found.")

print(f"Results have been saved to Tags.txt")
