import { Expense } from '../models/expense';

export class ExpenseService {
    private expenses: Expense[] = [];

    public addExpense(expense: Expense): void {
        this.expenses.push(expense);
    }

    public updateExpense(id: number, updatedExpense: Expense): boolean {
        const index = this.expenses.findIndex(exp => exp.id === id);
        if (index !== -1) {
            this.expenses[index] = updatedExpense;
            return true;
        }
        return false;
    }

    public getExpenses(): Expense[] {
        return this.expenses;
    }

    public deleteExpense(id: number): boolean {
        const index = this.expenses.findIndex(exp => exp.id === id);
        if (index !== -1) {
            this.expenses.splice(index, 1);
            return true;
        }
        return false;
    }
}