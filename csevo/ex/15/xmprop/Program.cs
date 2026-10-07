// 슬라이드 p15-v14-ext-prop — 확장 속성의 get 과 set, C# 14
using System;
using System.Linq;
using System.Reflection;
using System.Text;

static class SbExt
{
    extension(StringBuilder sb)
    {
        public bool IsEmpty => sb.Length == 0;    // get only
        public string Text                        // get and set
        {
            get => sb.ToString();
            set { sb.Clear(); sb.Append(value); }
        }
    }
}

class Program
{
    static void Main()
    {
        var sb = new StringBuilder();
        Console.WriteLine(sb.IsEmpty);
        sb.Text = "abc";
        sb.Text += "def";                 // get, then set
        Console.WriteLine(sb.Text + " " + sb.IsEmpty);
        foreach (MethodInfo m in typeof(SbExt).GetMethods(
            BindingFlags.Public | BindingFlags.Static
            | BindingFlags.DeclaredOnly).OrderBy(m => m.Name))
            Console.WriteLine(m);
    }
}
