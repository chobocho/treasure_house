// 슬라이드 p13-v12-pc-valid — 검사는 초기화자에서, C# 12.0
using System;

class Order(string id, int qty)
{
    public string Id { get; } =
        string.IsNullOrEmpty(id)
            ? throw new ArgumentException("empty id", nameof(id))
            : id;
    public int Qty { get; } = qty > 0
        ? qty
        : throw new ArgumentOutOfRangeException(nameof(qty));
}

class App
{
    static void Try(string id, int qty)
    {
        try
        {
            var o = new Order(id, qty);
            Console.WriteLine($"ok {o.Id} {o.Qty}");
        }
        catch (ArgumentException e)
        {
            Console.WriteLine(e.GetType().Name + " " + e.ParamName);
        }
    }

    static void Main()
    {
        Try("A", 2);
        Try("", 2);
        Try("B", 0);
    }
}
