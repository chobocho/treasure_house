// 슬라이드 p3-v2-partial-method — partial 메서드, C# 3.0
using System;

partial class Customer
{
    partial void OnNameChanged()         // implemented: called
    {
        Console.WriteLine("name is now " + name);
    }                                    // OnSaved: not implemented
}

class App
{
    static void Main()
    {
        Customer c = new Customer();
        c.Name = "Ada";
        c.Save();
        Console.WriteLine(typeof(Customer).GetMethod("OnSaved",
            System.Reflection.BindingFlags.NonPublic |
            System.Reflection.BindingFlags.Instance) == null);
    }
}
