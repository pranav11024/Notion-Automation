import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import json
import os
import threading
import time
from datetime import datetime, timedelta
import requests
import re

class NotionAutomationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Notion AI Automation Manager")
        self.root.geometry("800x700")
        
        # Configuration
        self.config_file = "notion_config.json"
        self.tasks_file = "automation_tasks.json"
        self.load_config()
        
        # Running tasks
        self.running_tasks = {}
        self.stop_flags = {}
        
        self.create_widgets()
        self.load_tasks()
        
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            "notion_token": "",
            "default_database_id": "",
            "ai_provider": "gemini",  
            "gemini_api_key": "",
            "ai_model": "gemini-1.5-flash"
        }
        
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = default_config
            self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_widgets(self):
        """Create the main UI"""
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configuration Tab
        config_frame = ttk.Frame(notebook)
        notebook.add(config_frame, text="Configuration")
        self.create_config_tab(config_frame)
        
        # Tasks Tab
        tasks_frame = ttk.Frame(notebook)
        notebook.add(tasks_frame, text="Automation Tasks")
        self.create_tasks_tab(tasks_frame)
        
        # Manual Control Tab
        manual_frame = ttk.Frame(notebook)
        notebook.add(manual_frame, text="Manual Control")
        self.create_manual_tab(manual_frame)
        
        # Logs Tab
        logs_frame = ttk.Frame(notebook)
        notebook.add(logs_frame, text="Logs")
        self.create_logs_tab(logs_frame)
    
    def create_config_tab(self, parent):
        """Create configuration tab"""
        ttk.Label(parent, text="Notion Integration Token:").pack(anchor="w", pady=5)
        self.token_entry = ttk.Entry(parent, width=60, show="*")
        self.token_entry.pack(fill="x", padx=5)
        self.token_entry.insert(0, self.config.get("notion_token", ""))
        
        ttk.Label(parent, text="Default Database ID:").pack(anchor="w", pady=5)
        self.db_entry = ttk.Entry(parent, width=60)
        self.db_entry.pack(fill="x", padx=5)
        self.db_entry.insert(0, self.config.get("default_database_id", ""))
        
        ttk.Label(parent, text="AI Provider:").pack(anchor="w", pady=5)
        self.ai_provider = ttk.Combobox(parent, values=["gemini", "openai"], state="readonly")
        self.ai_provider.pack(fill="x", padx=5)
        self.ai_provider.set(self.config.get("ai_provider", "gemini"))
        
        ttk.Label(parent, text="Gemini API Key:").pack(anchor="w", pady=5)
        self.gemini_key_entry = ttk.Entry(parent, width=60, show="*")
        self.gemini_key_entry.pack(fill="x", padx=5)
        self.gemini_key_entry.insert(0, self.config.get("gemini_api_key", ""))
        
        ttk.Label(parent, text="AI Model:").pack(anchor="w", pady=5)
        self.ai_model_entry = ttk.Entry(parent, width=60)
        self.ai_model_entry.pack(fill="x", padx=5)
        self.ai_model_entry.insert(0, self.config.get("ai_model", "gemini-1.5-flash"))
        
        # Instructions for getting API key
        instructions = ttk.Label(parent, text="Get your Gemini API key from: https://makersuite.google.com/app/apikey", 
                               foreground="blue", cursor="hand2")
        instructions.pack(anchor="w", pady=5)
        
        ttk.Button(parent, text="Save Configuration", command=self.save_configuration).pack(pady=10)
        ttk.Button(parent, text="Test Connection", command=self.test_connection).pack(pady=5)
    
    def create_tasks_tab(self, parent):
        """Create automation tasks tab"""
        # Task creation frame
        create_frame = ttk.LabelFrame(parent, text="Create New Task")
        create_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(create_frame, text="Task Name:").pack(anchor="w")
        self.task_name_entry = ttk.Entry(create_frame, width=50)
        self.task_name_entry.pack(fill="x", padx=5)
        
        ttk.Label(create_frame, text="Natural Language Instruction:").pack(anchor="w", pady=(10,0))
        self.instruction_text = scrolledtext.ScrolledText(create_frame, height=4)
        self.instruction_text.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(create_frame, text="Frequency (minutes):").pack(anchor="w")
        self.frequency_entry = ttk.Entry(create_frame, width=20)
        self.frequency_entry.pack(anchor="w", padx=5)
        self.frequency_entry.insert(0, "60")
        
        ttk.Button(create_frame, text="Create Task", command=self.create_task).pack(pady=5)
        
        # Tasks list frame
        list_frame = ttk.LabelFrame(parent, text="Active Tasks")
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Tasks treeview
        self.tasks_tree = ttk.Treeview(list_frame, columns=("status", "frequency", "next_run"), show="tree headings")
        self.tasks_tree.heading("#0", text="Task Name")
        self.tasks_tree.heading("status", text="Status")
        self.tasks_tree.heading("frequency", text="Frequency (min)")
        self.tasks_tree.heading("next_run", text="Next Run")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tasks_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Task control buttons
        control_frame = ttk.Frame(list_frame)
        control_frame.pack(side="bottom", fill="x", pady=5)
        
        ttk.Button(control_frame, text="Start Task", command=self.start_task).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Stop Task", command=self.stop_task).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Delete Task", command=self.delete_task).pack(side="left", padx=5)
        ttk.Button(control_frame, text="Edit Task", command=self.edit_task).pack(side="left", padx=5)
    
    def create_manual_tab(self, parent):
        """Create manual control tab"""
        ttk.Label(parent, text="Manual Instruction:").pack(anchor="w", pady=5)
        self.manual_instruction = scrolledtext.ScrolledText(parent, height=6)
        self.manual_instruction.pack(fill="x", padx=5, pady=5)
        
        ttk.Button(parent, text="Execute Now", command=self.execute_manual).pack(pady=10)
        
        # Results display
        ttk.Label(parent, text="Execution Result:").pack(anchor="w", pady=(20,5))
        self.result_display = scrolledtext.ScrolledText(parent, height=10, state="disabled")
        self.result_display.pack(fill="both", expand=True, padx=5, pady=5)
    
    def create_logs_tab(self, parent):
        """Create logs tab"""
        self.logs_display = scrolledtext.ScrolledText(parent, state="disabled")
        self.logs_display.pack(fill="both", expand=True, padx=5, pady=5)
        
        ttk.Button(parent, text="Clear Logs", command=self.clear_logs).pack(pady=5)
    
    def log_message(self, message):
        """Add message to logs"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.logs_display.config(state="normal")
        self.logs_display.insert(tk.END, log_entry)
        self.logs_display.see(tk.END)
        self.logs_display.config(state="disabled")
        
        # Also print to console
        print(log_entry.strip())
    
    def save_configuration(self):
        """Save configuration settings"""
        self.config["notion_token"] = self.token_entry.get()
        self.config["default_database_id"] = self.db_entry.get()
        self.config["ai_provider"] = self.ai_provider.get()
        self.config["gemini_api_key"] = self.gemini_key_entry.get()
        self.config["ai_model"] = self.ai_model_entry.get()
        
        self.save_config()
        messagebox.showinfo("Success", "Configuration saved successfully!")
        self.log_message("Configuration updated")
    
    def test_connection(self):
        """Test Notion and AI connections"""
        # Test Notion connection
        headers = {
            "Authorization": f"Bearer {self.config['notion_token']}",
            "Notion-Version": "2022-06-28"
        }
        
        try:
            response = requests.get("https://api.notion.com/v1/users/me", headers=headers)
            if response.status_code == 200:
                notion_status = "✓ Notion: Connected"
            else:
                notion_status = f"✗ Notion: Error {response.status_code}"
        except Exception as e:
            notion_status = f"✗ Notion: {str(e)}"
        
        # Test AI connection
        try:
            ai_response = self.query_ai("Create a test task")
            if ai_response and self.parse_ai_response(ai_response):
                ai_status = "✓ Gemini: Connected"
            else:
                ai_status = "✗ Gemini: Invalid response or parsing failed"
        except Exception as e:
            ai_status = f"✗ Gemini: {str(e)}"
        
        messagebox.showinfo("Connection Test", f"{notion_status}\n{ai_status}")
        self.log_message(f"Connection test: {notion_status}, {ai_status}")
    
    def query_ai(self, instruction):
        """Query AI with natural language instruction"""
        if self.config["ai_provider"] == "gemini":
            return self.query_gemini(instruction)
        else:
            return self.query_openai(instruction)
    
    def query_gemini(self, instruction):
        """Query Google Gemini AI"""
        prompt = f"""
        Convert this natural language instruction into specific Notion API actions:
        "{instruction}"
        
        You must respond with ONLY a valid JSON object (no markdown, no explanation, no extra text) containing:
        - action: one of (create_page, update_page, query_database, create_database_entry)
        - parameters: relevant parameters for the action
        - explanation: brief explanation of what will be done
        
        For create_database_entry, use this format:
        {{
            "action": "create_database_entry",
            "parameters": {{
                "database_id": "default",
                "properties": {{
                    "Name": {{"title": [{{"text": {{"content": "Task Name"}}}}]}},
                    "Status": {{"select": {{"name": "To Do"}}}},
                    "Priority": {{"select": {{"name": "Medium"}}}},
                    "Due Date": {{"date": {{"start": "2024-01-01"}}}}
                }}
            }},
            "explanation": "Creates a new task entry with the specified name and status"
        }}
        
        For query_database, use this format:
        {{
            "action": "query_database",
            "parameters": {{
                "database_id": "default",
                "filter": {{
                    "property": "Status",
                    "select": {{
                        "equals": "To Do"
                    }}
                }}
            }},
            "explanation": "Queries database for specific entries"
        }}
        
        For update_page, use this format:
        {{
            "action": "update_page",
            "parameters": {{
                "page_id": "PLACEHOLDER_PAGE_ID",
                "properties": {{
                    "Status": {{"select": {{"name": "Done"}}}}
                }}
            }},
            "explanation": "Updates existing page properties"
        }}
        
        Remember: respond with ONLY the JSON object, nothing else.
        """
        
        try:
            api_key = self.config.get("gemini_api_key", "")
            if not api_key:
                self.log_message("Gemini API key not configured")
                return None
            
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config['ai_model']}:generateContent?key={api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": 0.1,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 2048,
                },
                "safetySettings": [
                    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
                    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"}
                ]
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return content.strip()
                else:
                    self.log_message("No response from Gemini")
                    return None
            else:
                self.log_message(f"Gemini API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.log_message(f"Gemini query error: {str(e)}")
            return None
    
    
    def parse_ai_response(self, ai_response):
        """Parse AI response and extract JSON"""
        try:
            # Clean the response - remove markdown code blocks if present
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]  # Remove ```json
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]   # Remove ```
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]  # Remove ending ```
            
            cleaned_response = cleaned_response.strip()
            
            # Try to parse as JSON directly first
            try:
                return json.loads(cleaned_response)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    self.log_message(f"No JSON found in AI response: {cleaned_response[:200]}...")
                    return None
                    
        except Exception as e:
            self.log_message(f"Failed to parse AI response: {str(e)}")
            self.log_message(f"Raw response: {ai_response[:200]}...")
            return None
    
    def execute_notion_action(self, action_data):
        """Execute the parsed action on Notion"""
        if not action_data:
            return False
        
        headers = {
            "Authorization": f"Bearer {self.config['notion_token']}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        try:
            action = action_data.get("action")
            params = action_data.get("parameters", {})
            
            if action == "create_database_entry":
                db_id = params.get("database_id")
                if db_id == "default":
                    db_id = self.config["default_database_id"]
                
                url = f"https://api.notion.com/v1/pages"
                payload = {
                    "parent": {"database_id": db_id},
                    "properties": params.get("properties", {})
                }
                
                response = requests.post(url, headers=headers, json=payload)
                
            elif action == "query_database":
                db_id = params.get("database_id", self.config["default_database_id"])
                url = f"https://api.notion.com/v1/databases/{db_id}/query"
                response = requests.post(url, headers=headers, json=params)
                
            elif action == "update_page":
                page_id = params.get("page_id")
                url = f"https://api.notion.com/v1/pages/{page_id}"
                payload = {"properties": params.get("properties", {})}
                response = requests.patch(url, headers=headers, json=payload)
            
            else:
                self.log_message(f"Unknown action: {action}")
                return False
            
            if response.status_code in [200, 201]:
                self.log_message(f"Successfully executed: {action_data.get('explanation', action)}")
                return True
            else:
                self.log_message(f"Notion API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_message(f"Error executing Notion action: {str(e)}")
            return False
    
    def create_task(self):
        """Create a new automation task"""
        name = self.task_name_entry.get().strip()
        instruction = self.instruction_text.get("1.0", tk.END).strip()
        frequency = self.frequency_entry.get().strip()
        
        if not name or not instruction:
            messagebox.showerror("Error", "Please provide task name and instruction")
            return
        
        try:
            frequency = int(frequency)
        except ValueError:
            messagebox.showerror("Error", "Frequency must be a number")
            return
        
        task = {
            "name": name,
            "instruction": instruction,
            "frequency": frequency,
            "status": "stopped",
            "next_run": None,
            "created": datetime.now().isoformat()
        }
        
        # Load existing tasks
        tasks = self.load_tasks_data()
        tasks[name] = task
        self.save_tasks_data(tasks)
        
        # Clear form
        self.task_name_entry.delete(0, tk.END)
        self.instruction_text.delete("1.0", tk.END)
        self.frequency_entry.delete(0, tk.END)
        self.frequency_entry.insert(0, "60")
        
        # Refresh tasks display
        self.load_tasks()
        self.log_message(f"Created task: {name}")
    
    def load_tasks_data(self):
        """Load tasks from file"""
        if os.path.exists(self.tasks_file):
            with open(self.tasks_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_tasks_data(self, tasks):
        """Save tasks to file"""
        with open(self.tasks_file, 'w') as f:
            json.dump(tasks, f, indent=2)
    
    def load_tasks(self):
        """Load and display tasks in the tree view"""
        # Clear existing items
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        tasks = self.load_tasks_data()
        for name, task in tasks.items():
            next_run = task.get("next_run", "Not scheduled")
            if next_run and next_run != "Not scheduled":
                try:
                    next_run = datetime.fromisoformat(next_run).strftime("%Y-%m-%d %H:%M")
                except:
                    next_run = "Invalid date"
            
            self.tasks_tree.insert("", tk.END, text=name, 
                                 values=(task["status"], task["frequency"], next_run))
    
    def start_task(self):
        """Start selected task"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to start")
            return
        
        task_name = self.tasks_tree.item(selection[0])["text"]
        tasks = self.load_tasks_data()
        
        if task_name in tasks:
            if task_name in self.running_tasks:
                messagebox.showinfo("Info", "Task is already running")
                return
            
            tasks[task_name]["status"] = "running"
            tasks[task_name]["next_run"] = (datetime.now() + timedelta(minutes=tasks[task_name]["frequency"])).isoformat()
            self.save_tasks_data(tasks)
            
            # Start task thread
            self.stop_flags[task_name] = False
            thread = threading.Thread(target=self.run_task, args=(task_name, tasks[task_name]))
            thread.daemon = True
            thread.start()
            self.running_tasks[task_name] = thread
            
            self.load_tasks()
            self.log_message(f"Started task: {task_name}")
    
    def stop_task(self):
        """Stop selected task"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to stop")
            return
        
        task_name = self.tasks_tree.item(selection[0])["text"]
        
        if task_name in self.running_tasks:
            self.stop_flags[task_name] = True
            del self.running_tasks[task_name]
            
            tasks = self.load_tasks_data()
            tasks[task_name]["status"] = "stopped"
            tasks[task_name]["next_run"] = None
            self.save_tasks_data(tasks)
            
            self.load_tasks()
            self.log_message(f"Stopped task: {task_name}")
        else:
            messagebox.showinfo("Info", "Task is not running")
    
    def delete_task(self):
        """Delete selected task"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to delete")
            return
        
        task_name = self.tasks_tree.item(selection[0])["text"]
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete task '{task_name}'?"):
            # Stop task if running
            if task_name in self.running_tasks:
                self.stop_flags[task_name] = True
                del self.running_tasks[task_name]
            
            # Remove from tasks
            tasks = self.load_tasks_data()
            if task_name in tasks:
                del tasks[task_name]
                self.save_tasks_data(tasks)
            
            self.load_tasks()
            self.log_message(f"Deleted task: {task_name}")
    
    def edit_task(self):
        """Edit selected task"""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to edit")
            return
        
        task_name = self.tasks_tree.item(selection[0])["text"]
        tasks = self.load_tasks_data()
        
        if task_name in tasks:
            task = tasks[task_name]
            
            # Populate form with existing values
            self.task_name_entry.delete(0, tk.END)
            self.task_name_entry.insert(0, task_name)
            
            self.instruction_text.delete("1.0", tk.END)
            self.instruction_text.insert("1.0", task["instruction"])
            
            self.frequency_entry.delete(0, tk.END)
            self.frequency_entry.insert(0, str(task["frequency"]))
            
            # Delete the existing task (will be recreated when user clicks Create Task)
            del tasks[task_name]
            self.save_tasks_data(tasks)
            self.load_tasks()
    
    def run_task(self, task_name, task_data):
        """Run a task in a loop"""
        while not self.stop_flags.get(task_name, False):
            try:
                self.log_message(f"Executing task: {task_name}")
                
                # Query AI for action
                ai_response = self.query_ai(task_data["instruction"])
                if ai_response:
                    action_data = self.parse_ai_response(ai_response)
                    if action_data:
                        success = self.execute_notion_action(action_data)
                        if success:
                            self.log_message(f"Task '{task_name}' completed successfully")
                        else:
                            self.log_message(f"Task '{task_name}' failed to execute")
                    else:
                        self.log_message(f"Task '{task_name}': Failed to parse AI response")
                else:
                    self.log_message(f"Task '{task_name}': No AI response")
                
                # Update next run time
                tasks = self.load_tasks_data()
                if task_name in tasks:
                    tasks[task_name]["next_run"] = (datetime.now() + timedelta(minutes=task_data["frequency"])).isoformat()
                    self.save_tasks_data(tasks)
                
                # Wait for the specified frequency
                for _ in range(task_data["frequency"] * 60):  # Convert minutes to seconds
                    if self.stop_flags.get(task_name, False):
                        break
                    time.sleep(1)
                
            except Exception as e:
                self.log_message(f"Error in task '{task_name}': {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
    
    def execute_manual(self):
        """Execute manual instruction"""
        instruction = self.manual_instruction.get("1.0", tk.END).strip()
        if not instruction:
            messagebox.showwarning("Warning", "Please enter an instruction")
            return
        
        self.result_display.config(state="normal")
        self.result_display.delete("1.0", tk.END)
        self.result_display.insert(tk.END, "Executing...\n")
        self.result_display.config(state="disabled")
        
        # Execute in a separate thread to avoid blocking UI
        thread = threading.Thread(target=self._execute_manual_thread, args=(instruction,))
        thread.daemon = True
        thread.start()
    
    def _execute_manual_thread(self, instruction):
        """Execute manual instruction in thread"""
        try:
            ai_response = self.query_ai(instruction)
            result_text = f"AI Response:\n{ai_response}\n\n"
            
            if ai_response:
                action_data = self.parse_ai_response(ai_response)
                if action_data:
                    result_text += f"Parsed Action:\n{json.dumps(action_data, indent=2)}\n\n"
                    
                    success = self.execute_notion_action(action_data)
                    if success:
                        result_text += "✓ Successfully executed on Notion"
                    else:
                        result_text += "✗ Failed to execute on Notion"
                else:
                    result_text += "✗ Failed to parse AI response"
            else:
                result_text += "✗ No response from AI"
            
            # Update UI from main thread
            self.root.after(0, self._update_manual_result, result_text)
            
        except Exception as e:
            error_text = f"Error: {str(e)}"
            self.root.after(0, self._update_manual_result, error_text)
    
    def _update_manual_result(self, text):
        """Update manual result display"""
        self.result_display.config(state="normal")
        self.result_display.delete("1.0", tk.END)
        self.result_display.insert(tk.END, text)
        self.result_display.config(state="disabled")
    
    def clear_logs(self):
        """Clear the logs display"""
        self.logs_display.config(state="normal")
        self.logs_display.delete("1.0", tk.END)
        self.logs_display.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = NotionAutomationApp(root)
    root.mainloop()