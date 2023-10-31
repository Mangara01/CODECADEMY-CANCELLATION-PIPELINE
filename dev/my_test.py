import logging
import sqlite3
import pandas as pd
import unittest

db_path = 'cademycode.db'

logging.basicConfig(filename='error.log', level=logging.ERROR, filemode='w')

class TestDatabaseUpdate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            conn = sqlite3.connect(db_path)
            query = "SELECT name FROM sqlite_master WHERE type='table';"
            tables = pd.read_sql_query(query, conn)

            dataframes = {}
            for table_name in tables['name']:
                query = f"SELECT * FROM {table_name};"
                df = pd.read_sql_query(query, conn)

                df.dropna(inplace=True)

                if 'current_career_path_id' in df.columns:
                    df['current_career_path_id'] = pd.to_numeric(df['current_career_path_id'], errors='coerce', downcast='integer')
                if 'job_id' in df.columns:
                    df['job_id'] = pd.to_numeric(df['job_id'], errors='coerce', downcast='integer')

                if table_name == 'cademycode_students':
                    df.rename(columns={'current_career_path_id': 'career_path_id'}, inplace=True)

                dataframes[table_name] = df

            merged_data = None
            table_order = ['cademycode_students', 'cademycode_courses', 'cademycode_student_jobs']

            for table_name in table_order:
                df = dataframes.get(table_name)
                if merged_data is None:
                    merged_data = df
                else:
                    if table_name == 'cademycode_students':
                        merged_data = pd.merge(merged_data, df, on=['career_path_id', 'job_id'], how='inner')
                    elif table_name == 'cademycode_courses':
                        merged_data = pd.merge(merged_data, df, on='career_path_id', how='inner')
                    else:
                        merged_data = pd.merge(merged_data, df, on='job_id', how='inner')

            cls.merged_data = merged_data
            conn.close()

        except Exception as e:
            logging.error(f"Error during database update: {str(e)}")

    def test_schema_consistency(self):
        original_tables = ['uuid','name','dob','sex','contact_info','job_id','num_course_taken','career_path_id','time_spent_hrs','career_path_name','hours_to_complete','job_category','avg_salary']
        updated_tables = self.merged_data.columns.tolist()
        self.assertListEqual(original_tables, updated_tables, "Schema consistency test failed")

    def test_new_data(self):
        original_record_count = 6022 
        updated_record_count = len(self.merged_data)
        self.assertGreaterEqual(updated_record_count, original_record_count, "New data test failed")

if __name__ == '__main__':
    changelog = open('changelog.txt', 'w')  
    changelog_text = "Version 1.0 - Update details: New data added"
    changelog.write(changelog_text)
    changelog.close()
    unittest.main()