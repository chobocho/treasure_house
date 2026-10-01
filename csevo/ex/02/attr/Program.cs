// 슬라이드 p2-v1-attr — 내가 만드는 특성, C# 1.0
using System;
using System.Reflection;

[AttributeUsage(AttributeTargets.Method, AllowMultiple = true)]
class OwnerAttribute : Attribute
{
    public readonly string Name;
    public int Priority;                          // named parameter
    public OwnerAttribute(string name) { Name = name; }  // positional
}

class Jobs
{
    [Owner("kim")]
    public void Backup() { }

    [Owner("lee", Priority = 2)]
    [Owner("park")]
    public void Report() { }

    public void Idle() { }
}

class App
{
    static void Main()
    {
        string[] names = { "Backup", "Report", "Idle" };
        foreach (string m in names)
        {
            MethodInfo mi = typeof(Jobs).GetMethod(m);
            object[] a = mi.GetCustomAttributes(typeof(OwnerAttribute),
                false);
            string who = "";
            foreach (OwnerAttribute o in a)
                who += " " + o.Name + "/" + o.Priority;
            Console.WriteLine(m + ":" + (a.Length == 0 ? " -" : who));
        }
    }
}
