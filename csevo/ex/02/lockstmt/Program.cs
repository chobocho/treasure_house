// 슬라이드 p2-v1-lock — lock 은 Monitor 의 줄임, C# 1.0
using System;
using System.Threading;

class Account
{
    readonly object gate = new object();
    decimal balance;

    public void Deposit(decimal amount)
    {
        lock (gate)
        {
            balance += amount;
            Console.WriteLine("  held: " + Monitor.IsEntered(gate));
            if (amount > 100) Deposit(-1);   // re-entry: same thread
        }
    }

    public void Withdraw(decimal amount)   // as the standard expands it
    {
        bool taken = false;
        try
        {
            Monitor.Enter(gate, ref taken);
            balance -= amount;
        }
        finally { if (taken) Monitor.Exit(gate); }
    }

    public decimal Balance { get { return balance; } }
    public bool Held { get { return Monitor.IsEntered(gate); } }
}

class App
{
    static void Main()
    {
        Account a = new Account();
        a.Deposit(500);
        a.Withdraw(99);
        Console.WriteLine("balance " + a.Balance + ", held: " + a.Held);
    }
}
