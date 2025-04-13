
import os
import sys
from app import app, db
from sqlalchemy import text, inspect
from models import Club, ClubMembership, ClubPost, ClubResource, ClubChatChannel, ClubChatMessage, ClubAssignment

def get_table_columns(table_name):
    """Get all columns for a specific table"""
    with app.app_context():
        inspector = inspect(db.engine)
        return [column['name'] for column in inspector.get_columns(table_name)]

def fix_club_tables():
    """Comprehensive database schema fixer for club-related tables"""
    with app.app_context():
        print("Starting comprehensive database schema fix...")
        
        # Fix any pending transactions first
        db.session.rollback()
        
        # Fix club_post table
        try:
            print("\n--- Fixing club_post table ---")
            columns = get_table_columns('club_post')
            print(f"Current columns: {', '.join(columns)}")
            
            # Handle column renames and additions
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    -- Handle author_id to user_id conversion if needed
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'club_post' AND column_name = 'author_id'
                    ) THEN
                        ALTER TABLE club_post RENAME COLUMN author_id TO user_id;
                        RAISE NOTICE 'Renamed author_id to user_id';
                    END IF;
                    
                    -- Add user_id if it doesn't exist
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'club_post' AND column_name = 'user_id'
                    ) THEN
                        ALTER TABLE club_post ADD COLUMN user_id INTEGER REFERENCES "user"(id);
                        RAISE NOTICE 'Added user_id column';
                    END IF;
                    
                    -- Make sure there's no NOT NULL constraint if we just added it
                    BEGIN
                        ALTER TABLE club_post ALTER COLUMN user_id DROP NOT NULL;
                        RAISE NOTICE 'Dropped NOT NULL constraint from user_id';
                    EXCEPTION WHEN OTHERS THEN
                        NULL;
                    END;
                END $$;
            """))
            db.session.commit()
            print("✅ Successfully fixed club_post table schema")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_post table: {str(e)}")
        
        # Fix club_resource table
        try:
            print("\n--- Fixing club_resource table ---")
            columns = get_table_columns('club_resource')
            print(f"Current columns: {', '.join(columns)}")
            
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    -- Handle creator_id to created_by conversion if needed
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'club_resource' AND column_name = 'creator_id'
                    ) THEN
                        ALTER TABLE club_resource RENAME COLUMN creator_id TO created_by;
                        RAISE NOTICE 'Renamed creator_id to created_by';
                    END IF;
                    
                    -- Add created_by if it doesn't exist
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'club_resource' AND column_name = 'created_by'
                    ) THEN
                        ALTER TABLE club_resource ADD COLUMN created_by INTEGER REFERENCES "user"(id);
                        RAISE NOTICE 'Added created_by column';
                    END IF;
                    
                    -- Make sure there's no NOT NULL constraint if we just added it
                    BEGIN
                        ALTER TABLE club_resource ALTER COLUMN created_by DROP NOT NULL;
                        RAISE NOTICE 'Dropped NOT NULL constraint from created_by';
                    EXCEPTION WHEN OTHERS THEN
                        NULL;
                    END;
                END $$;
            """))
            db.session.commit()
            print("✅ Successfully fixed club_resource table schema")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_resource table: {str(e)}")
        
        # Fix club_assignment table
        try:
            print("\n--- Fixing club_assignment table ---")
            columns = get_table_columns('club_assignment')
            print(f"Current columns: {', '.join(columns)}")
            
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    -- Add is_active column if it doesn't exist
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'club_assignment' AND column_name = 'is_active'
                    ) THEN
                        ALTER TABLE club_assignment ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
                        RAISE NOTICE 'Added is_active column';
                    END IF;
                    
                    -- Add created_by if it doesn't exist
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'club_assignment' AND column_name = 'created_by'
                    ) THEN
                        ALTER TABLE club_assignment ADD COLUMN created_by INTEGER REFERENCES "user"(id);
                        RAISE NOTICE 'Added created_by column';
                    END IF;
                    
                    -- Make sure there's no NOT NULL constraint if we just added it
                    BEGIN
                        ALTER TABLE club_assignment ALTER COLUMN created_by DROP NOT NULL;
                        RAISE NOTICE 'Dropped NOT NULL constraint from created_by';
                    EXCEPTION WHEN OTHERS THEN
                        NULL;
                    END;
                END $$;
            """))
            db.session.commit()
            print("✅ Successfully fixed club_assignment table schema")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_assignment table: {str(e)}")
            
        # Fix club_chat_message table
        try:
            print("\n--- Fixing club_chat_message table ---")
            columns = get_table_columns('club_chat_message')
            print(f"Current columns: {', '.join(columns)}")
            
            db.session.execute(text("""
                DO $$ 
                BEGIN
                    -- Make sure channel_id can be NULL to allow direct messages
                    IF EXISTS (
                        SELECT 1 FROM information_schema.columns 
                        WHERE table_name = 'club_chat_message' AND column_name = 'channel_id'
                    ) THEN
                        BEGIN
                            ALTER TABLE club_chat_message ALTER COLUMN channel_id DROP NOT NULL;
                            RAISE NOTICE 'Dropped NOT NULL constraint from channel_id';
                        EXCEPTION WHEN OTHERS THEN
                            NULL;
                        END;
                    END IF;
                END $$;
            """))
            db.session.commit()
            print("✅ Successfully fixed club_chat_message table schema")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error fixing club_chat_message table: {str(e)}")
            
        print("\nDatabase schema fixes completed.")

def create_default_channels():
    """Create default channels for all clubs if they don't have any"""
    with app.app_context():
        print("\nChecking and creating default channels for clubs...")
        
        try:
            clubs = Club.query.all()
            
            for club in clubs:
                # Check if club already has channels
                existing_channels = ClubChatChannel.query.filter_by(club_id=club.id).count()
                
                if existing_channels == 0:
                    # Create default channels
                    default_channels = [
                        {"name": "general", "description": "General discussions"},
                        {"name": "announcements", "description": "Important announcements"},
                        {"name": "help", "description": "Get help with your projects"}
                    ]
                    
                    print(f"Creating default channels for club: {club.name}")
                    
                    for channel_data in default_channels:
                        channel = ClubChatChannel(
                            club_id=club.id,
                            name=channel_data["name"],
                            description=channel_data["description"],
                            created_by=club.leader_id
                        )
                        db.session.add(channel)
                    
                    db.session.commit()
                    print(f"Created default channels for club: {club.name}")
                else:
                    print(f"Club already has channels: {club.name} ({existing_channels} channels)")
            
            print("✅ Completed channel setup")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating default channels: {str(e)}")

if __name__ == "__main__":
    fix_club_tables()
    create_default_channels()
