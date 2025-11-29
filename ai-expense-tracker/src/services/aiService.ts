import axios from 'axios';

export class AIService {
    private apiUrl: string;

    constructor(apiUrl: string) {
        this.apiUrl = apiUrl;
    }

    public async analyzeExpenses(expenses: any[]): Promise<any> {
        try {
            const response = await axios.post(`${this.apiUrl}/analyze`, { expenses });
            return response.data;
        } catch (error) {
            throw new Error('Error analyzing expenses: ' + error.message);
        }
    }

    public async getRecommendations(userId: string): Promise<any> {
        try {
            const response = await axios.get(`${this.apiUrl}/recommendations/${userId}`);
            return response.data;
        } catch (error) {
            throw new Error('Error fetching recommendations: ' + error.message);
        }
    }
}