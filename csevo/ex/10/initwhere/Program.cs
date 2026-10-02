// 슬라이드 p10-v9-init-where — init 을 부를 수 있는 곳, C# 9.0
using System;

class NoteAttribute : Attribute
{
    public string Text { get; init; }
}

class Base
{
    public string Name { get; init; }
}

[Note(Text = "attr")]                        // 5. attribute argument
class Derived : Base
{
    public Derived() { Name = "ctor"; }      // 3. derived constructor
    public string Alias
    {
        get => Name;
        init => Name = value;                // 4. another init
    }
}

record Rec(string Name);

class App
{
    static void Main()
    {
        var d = new Derived { Name = "init" };  // 1. object initializer
        var e = new Derived { Alias = "alias" };
        var r = new Rec("a") with { Name = "with" }; // 2. with
        Console.WriteLine(d.Name + " " + e.Name + " " + r.Name);
        Console.WriteLine(new Derived().Name);
        var note = (NoteAttribute)Attribute.GetCustomAttribute(
            typeof(Derived), typeof(NoteAttribute));
        Console.WriteLine(note.Text);
    }
}
