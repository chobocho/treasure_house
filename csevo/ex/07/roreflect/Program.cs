// 슬라이드 p7-v6-roauto-reflect — readonly 와 리플렉션, C# 6.0
using System;
using System.Reflection;

class Holder
{
    public int Value { get; } = 1;
    public static int Shared { get; } = 1;
}

class Program
{
    static void Main()
    {
        BindingFlags nonPub = BindingFlags.NonPublic;
        Holder h = new Holder();
        FieldInfo inst = typeof(Holder).GetField(
            "<Value>k__BackingField", nonPub | BindingFlags.Instance);
        inst.SetValue(h, 42);
        Console.WriteLine("Value = " + h.Value);

        FieldInfo stat = typeof(Holder).GetField(
            "<Shared>k__BackingField", nonPub | BindingFlags.Static);
        Console.WriteLine("Shared = " + Holder.Shared);
        try
        {
            stat.SetValue(null, 42);
        }
        catch (FieldAccessException e)
        {
            Console.WriteLine(e.GetType().Name + ": " + e.Message);
        }
        Console.WriteLine("Shared = " + Holder.Shared);
    }
}
