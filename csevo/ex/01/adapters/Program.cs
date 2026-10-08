// 슬라이드 p1-java-count — 메뉴 셋, 대리자 셋, C# 1.0
using System;
using System.Reflection;

delegate void Action1(string command);

class MenuItem
{
    public string Text;
    public Action1 Handler;
    public MenuItem(string text) { Text = text; }
    public void Click() { Handler(Text); }
}

class Editor
{
    MenuItem open = new MenuItem("Open"), save = new MenuItem("Save"),
             exit = new MenuItem("Exit");

    void NotYet(string what)
    {
        Console.WriteLine(what + ": not implemented");
    }
    Editor()
    {
        open.Handler = new Action1(NotYet);
        save.Handler = new Action1(NotYet);
        exit.Handler = new Action1(NotYet);
    }
    static void Main()
    {
        Editor e = new Editor();
        e.open.Click(); e.save.Click(); e.exit.Click();
        Type[] types = Assembly.GetExecutingAssembly().GetTypes();
        string[] names = new string[types.Length];
        for (int i = 0; i < types.Length; i++) names[i] = types[i].Name;
        Array.Sort(names, StringComparer.Ordinal);
        Console.WriteLine(types.Length + " types: "
            + String.Join(" ", names));
    }
}
