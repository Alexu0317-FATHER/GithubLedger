import { Router } from 'express';
import ExpenseController from '../controllers/expenseController';
import AIController from '../controllers/aiController';

const router = Router();
const expenseController = new ExpenseController();
const aiController = new AIController();

router.post('/expenses', expenseController.createExpense.bind(expenseController));
router.get('/expenses', expenseController.getExpenses.bind(expenseController));
router.delete('/expenses/:id', expenseController.deleteExpense.bind(expenseController));

router.post('/analyze', aiController.analyzeExpenses.bind(aiController));
router.get('/recommendations', aiController.getRecommendations.bind(aiController));

export default router;