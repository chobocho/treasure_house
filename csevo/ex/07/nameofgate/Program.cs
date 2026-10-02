// 슬라이드 p7-v6-nameof-gate — nameof 식, C# 6.0
using System;

class Account
{
    public decimal Balance;
    public void Deposit(decimal amount) { Balance += amount; }
}

class App
{
    static void Main()
    {
        var acct = new Account();
        int retries = 3;
        Console.WriteLine(nameof(retries));            // local
        Console.WriteLine(nameof(acct));               // local
        Console.WriteLine(nameof(acct.Balance));       // field
        Console.WriteLine(nameof(Account.Deposit));    // method
        Console.WriteLine(nameof(Account));            // type
        Console.WriteLine(nameof(Main));               // this method
        Console.WriteLine(nameof(retries).GetType().Name);
    }
}
