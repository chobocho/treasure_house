// 슬라이드 p13-v12-primary — 클래스의 기본 생성자, C# 12.0
using System;

class Account(string id, string owner, decimal balance)
{
    public string Id { get; } = id;              // initializer
    public string Owner => owner;                // member body

    public void Deposit(decimal amount) => balance += amount;

    public override string ToString() =>
        $"{Id} {owner} {balance}";
}

class App
{
    static void Main()
    {
        var a = new Account("A-1", "Kim", 100m);
        a.Deposit(50m);
        Console.WriteLine(a);
        Console.WriteLine(a.Owner);
    }
}
