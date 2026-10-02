// 슬라이드 p7-v6-autoinit-virtual — 초기화자와 재정의된 set, C# 6.0
using System;

class Base
{
    public virtual bool IsActive { get; set; } = true;
}

class Derived : Base
{
    public override bool IsActive
    {
        get { return base.IsActive; }
        set
        {
            base.IsActive = value;
            Console.WriteLine("  override setter: " + value);
        }
    }

    public Derived() { }

    public Derived(bool active)
    {
        IsActive = active;
    }
}

class Program
{
    static void Main()
    {
        Console.WriteLine("new Derived():");
        Console.WriteLine("  IsActive = " + new Derived().IsActive);
        Console.WriteLine("new Derived(true):");
        new Derived(true);
    }
}
