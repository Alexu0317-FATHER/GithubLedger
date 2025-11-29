import { Request, Response } from 'express';
import { AIService } from '../services/aiService';

export class AIController {
    private aiService: AIService;

    constructor() {
        this.aiService = new AIService();
    }

    public analyzeExpenses = async (req: Request, res: Response): Promise<void> => {
        try {
            const analysisResult = await this.aiService.analyzeExpenses(req.body.expenses);
            res.status(200).json(analysisResult);
        } catch (error) {
            res.status(500).json({ message: 'Error analyzing expenses', error });
        }
    };

    public getRecommendations = async (req: Request, res: Response): Promise<void> => {
        try {
            const recommendations = await this.aiService.getRecommendations(req.body.userId);
            res.status(200).json(recommendations);
        } catch (error) {
            res.status(500).json({ message: 'Error getting recommendations', error });
        }
    };
}