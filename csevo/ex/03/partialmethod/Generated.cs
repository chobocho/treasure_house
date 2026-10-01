// 슬라이드 p3-v2-partial-method — 도구가 만든 쪽, C# 3.0
using System;

partial class Customer
{
    string name;
    partial void OnNameChanged();        // a hook, maybe unused
    partial void OnSaved();

    public string Name
    {
        get { return name; }
        set { name = value; OnNameChanged(); }
    }

    public void Save() { OnSaved(); Console.WriteLine("saved"); }
}
