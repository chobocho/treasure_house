// 슬라이드 p7-v6-nameof-inst12 — 인스턴스 멤버 거치기, C# 12.0
using System;

class Order
{
    public string Customer = "";
    public int[] Lines = { };

    public static string Describe()
    {
        // static context: no instance, but nameof does not evaluate
        return nameof(Customer.Length) + ", " +
            nameof(Lines.Rank) + ", " + nameof(Customer.ToString);
    }
}

class App
{
    static void Main()
    {
        Console.WriteLine(Order.Describe());
    }
}
