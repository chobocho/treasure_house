// 슬라이드 p4-v3-autoprop-field — 숨은 뒷받침 필드, C# 3.0
using System;
using System.Reflection;
using System.Runtime.CompilerServices;

class Person
{
    public string Name { get; set; }
    public int Age { get; private set; }
    public void Birthday() { Age++; }
}

class App
{
    static void Main()
    {
        Person p = new Person();
        p.Name = "Ann";
        p.Birthday();
        foreach (FieldInfo f in typeof(Person).GetFields(
            BindingFlags.NonPublic | BindingFlags.Instance))
        {
            Console.WriteLine(f.Name + " : " + f.FieldType.Name
                + " = " + f.GetValue(p));
            Console.WriteLine("  private=" + f.IsPrivate
                + ", generated=" + f.IsDefined(
                    typeof(CompilerGeneratedAttribute), false));
        }
        MethodInfo set =
            typeof(Person).GetProperty("Age").GetSetMethod(true);
        Console.WriteLine("Age setter: private=" + set.IsPrivate);
    }
}
