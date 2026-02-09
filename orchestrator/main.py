# Inside the /orchestrate endpoint...

# 3. Quality Assurance
tst_art = await tester.run(code_artifact_id=cod_art.artifact_id, db=db)

# 4. Feedback Loop Check (New Phase 2 Logic)
if tst_art.metadata["status"] == "FAILED":
    print(f"🔄 Feedback Loop Triggered: {tst_art.metadata['critique_points']}")
    
    # Re-task Coder with the critique
    cod_art = await coder.run(
        research_artifact=res_art, 
        critique=tst_art.content  # Coder needs a 'critique' parameter now
    )
    # Save the V2 Code to DB...
    
    # Final Verification
    tst_art = await tester.run(code_artifact_id=cod_art.artifact_id, db=db)

# Final Save and Return...
