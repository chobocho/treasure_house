// 슬라이드 p13-v12-nm-attr — 특성 인수 안의 nameof, C# 12.0
using System;
using System.ComponentModel;

class Order
{
    public string Customer = "";

    [Description(nameof(Customer.Length))]   // attribute argument
    public int Size => Customer.Length;
}

class App
{
    static void Main()
    {
        var prop = typeof(Order).GetProperty("Size");
        var d = (DescriptionAttribute)Attribute.GetCustomAttribute(
            prop, typeof(DescriptionAttribute));
        Console.WriteLine(prop.Name + " -> " + d.Description);
    }
}
