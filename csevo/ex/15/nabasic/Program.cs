// 슬라이드 p15-v14-nullassign — null 조건 대입, C# 14
using System;

class Customer
{
    public string Order;
    public void SetOrder(string o) { Order = o; }
}

class Program
{
    static readonly Customer ada = new Customer();

    static Customer Find(string name)
    {
        Console.WriteLine("  Find(" + name + ")");
        return name == "ada" ? ada : null;
    }

    static string GetOrder(string tag)
    {
        Console.WriteLine("  GetOrder(" + tag + ")");
        return tag;
    }

    static void Main()
    {
        Find("ada")?.Order = GetOrder("A1");      // C# 14
        Find("bob")?.Order = GetOrder("B1");      // right side skipped
        Find("bob")?.SetOrder(GetOrder("B2"));    // C# 6: same rule
        Console.WriteLine("ada.Order = " + ada.Order);
    }
}
