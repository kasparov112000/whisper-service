const { MongoClient, ObjectId } = require('mongodb');

async function fixTranscript() {
  const client = new MongoClient('mongodb://localhost:27017');
  await client.connect();

  const db = client.db('mdr-video-transcriptions');
  const result = await db.collection('video-transcriptions').updateOne(
    { _id: new ObjectId('692eb7ef01157f0920a82306') },
    {
      $set: {
        status: 'completed',
        progress: 100,
        errorMessage: ''
      }
    }
  );

  console.log('Updated:', result.modifiedCount);

  // Verify
  const doc = await db.collection('video-transcriptions').findOne(
    { _id: new ObjectId('692eb7ef01157f0920a82306') },
    { projection: { status: 1, progress: 1, transcript: 1 } }
  );
  console.log('Status:', doc.status);
  console.log('Progress:', doc.progress);
  console.log('Transcript length:', doc.transcript.length);
  console.log('First 500 chars:', doc.transcript.substring(0, 500));

  await client.close();
}

fixTranscript();
