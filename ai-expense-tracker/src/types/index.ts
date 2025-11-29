export interface Expense {
    id: string;
    amount: number;
    date: Date;
    category: string;
}

export interface Category {
    id: string;
    name: string;
}