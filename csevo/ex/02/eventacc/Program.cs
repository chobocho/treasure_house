// 슬라이드 p2-v1-eventacc — 이벤트 접근자 add·remove, C# 1.0
using System;
using System.Reflection;

class Button
{
    public event EventHandler Click;          // field-like

    EventHandler hover;                       // storage, by hand
    public event EventHandler Hover
    {
        add { Console.WriteLine("  add Hover"); hover += value; }
        remove { Console.WriteLine("  remove Hover"); hover -= value; }
    }

    public void Touch() { Click(this, EventArgs.Empty); }
}

class App
{
    static void OnAny(object s, EventArgs e) { }

    static void Main()
    {
        Button b = new Button();
        b.Hover += new EventHandler(OnAny);
        b.Hover -= new EventHandler(OnAny);

        BindingFlags all = BindingFlags.Instance | BindingFlags.Public
            | BindingFlags.NonPublic | BindingFlags.DeclaredOnly;
        foreach (string kind in new string[] { "fields", "methods" })
        {
            MemberInfo[] ms = kind == "fields"
                ? (MemberInfo[])typeof(Button).GetFields(all)
                : typeof(Button).GetMethods(all);
            string[] names = new string[ms.Length];
            for (int i = 0; i < ms.Length; i++) names[i] = ms[i].Name;
            Array.Sort(names);
            Console.WriteLine(kind + ": " + String.Join(" ", names));
        }
    }
}
