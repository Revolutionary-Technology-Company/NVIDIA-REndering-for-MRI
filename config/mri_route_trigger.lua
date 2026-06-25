-- Execute every time a scanner pushes a new file instance to the RTX 6000 Node
function OnStoredInstance(instanceId, tags, metadata)
   
   -- Extract file path inside the shared Docker spool volume
   local dicomPath = '/var/lib/orthanc/db/' .. string.sub(instanceId, 1, 2) .. '/' .. string.sub(instanceId, 3, 4) .. '/' .. instanceId
   local outputPath = '/tmp/' .. instanceId .. '_anon.dcm'
   
   -- Execute the Python anonymizer pipeline script
   local cmd = 'python3 /workspace/pipeline/pipelines/anonymize.py ' .. dicomPath .. ' ' .. outputPath .. ' ANON_MR_ROUTED'
   local success = os.execute(cmd)
   
   if success then
      -- Forward the newly anonymized file directly to the Cloud PACS array
      SendToModality(outputPath, 'CLOUD_PACS')
      
      -- Housekeeping: Flush the temp file from memory
      os.remove(outputPath)
   else
      print('[ERROR] NVIDIA pipeline execution failed for instance: ' .. instanceId)
   end
end
