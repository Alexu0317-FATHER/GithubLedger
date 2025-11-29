import { Request, Response } from 'express';
import { ExpenseService } from '../services/expenseService';
import { Expense } from '../models/expense';

export class ExpenseController {
    private expenseService: ExpenseService;

    constructor() {
        this.expenseService = new ExpenseService();
    }

    public createExpense = async (req: Request, res: Response): Promise<void> => {
        try {
            const expenseData: Expense = req.body;
            const newExpense = await this.expenseService.addExpense(expenseData);
            res.status(201).json(newExpense);
        } catch (error) {
            res.status(400).json({ message: error.message });
        }
    };

    public getExpenses = async (req: Request, res: Response): Promise<void> => {
        try {
            const expenses = await this.expenseService.getAllExpenses();
            res.status(200).json(expenses);
        } catch (error) {
            res.status(500).json({ message: error.message });
        }
    };

    public deleteExpense = async (req: Request, res: Response): Promise<void> => {
        try {
            const { id } = req.params;
            await this.expenseService.deleteExpense(id);
            res.status(204).send();
        } catch (error) {
            res.status(404).json({ message: error.message });
        }
    };
}