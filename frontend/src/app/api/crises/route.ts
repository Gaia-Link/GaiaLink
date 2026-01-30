import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs';

export async function GET() {
    try {
        // Locate the backend_data/data.json file relative to the project root
        const dataPath = path.join(process.cwd(), '..', 'backend_data', 'data.json');

        // Check if file exists
        if (!fs.existsSync(dataPath)) {
            console.error("Data file not found at:", dataPath);
            return NextResponse.json({ crises: [], proposals: [] }, { status: 404 });
        }

        const fileContents = fs.readFileSync(dataPath, 'utf8');
        const data = JSON.parse(fileContents);

        return NextResponse.json(data);
    } catch (error) {
        console.error("Error reading crisis data:", error);
        return NextResponse.json({ error: 'Failed to load crisis data' }, { status: 500 });
    }
}
