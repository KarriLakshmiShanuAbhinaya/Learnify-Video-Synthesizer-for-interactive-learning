import sys
import os

# Add the current directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from ai_service import generate_mcqs

def test_adaptive_mcqs():
    text = """
    Python is a popular programming language. 
    Recursion is a technique where a function calls itself. 
    Loops are used for iteration. 
    Data structures index elements starting from zero.
    Functions should be modular.
    """
    
    # Previous analysis highlights "Recursion" as a weak area
    previous_analysis = """
    Strengths
    Basic Python logic.
    
    Areas for Improvement
    Students struggled with Recursion and function calls.
    
    Recommended Topics
    - Recursion: Deep dive into base cases.
    """
    
    print("--- Generating MCQs WITHOUT previous analysis ---")
    mcqs_normal = generate_mcqs(text, num_questions=3)
    for i, m in enumerate(mcqs_normal):
        print(f"{i+1}. {m['question']} (Answer: {m['answer']})")
    
    print("\n--- Generating MCQs WITH previous analysis (Focus on Recursion) ---")
    mcqs_adaptive = generate_mcqs(text, num_questions=3, previous_analysis=previous_analysis)
    found_recursion = False
    for i, m in enumerate(mcqs_adaptive):
        print(f"{i+1}. {m['question']} (Answer: {m['answer']})")
        if "Recursion" in m['answer'] or "Recursion" in m['question'] or "recursion" in m['question'].lower():
            found_recursion = True
            
    if found_recursion:
        print("\n✅ SUCCESS: Adaptive MCQ included targeted topic 'Recursion'.")
    else:
        print("\n❌ FAILURE: Adaptive MCQ did not prioritize 'Recursion'.")

if __name__ == "__main__":
    test_adaptive_mcqs()
