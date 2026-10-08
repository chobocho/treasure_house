// 슬라이드 p1-design-comp-cs — 속성·이벤트·특성이 메타데이터로, C# 1.0
using System;
using System.ComponentModel;
using System.Reflection;

class Person
{
    string name;
    public event EventHandler NameChanged;

    [Category("Identity"), Description("Display name")]
    public string Name
    {
        get { return name; }
        set
        {
            name = value;
            if (NameChanged != null) NameChanged(this, EventArgs.Empty);
        }
    }

    static void Changed(object sender, EventArgs e)
    {
        Console.WriteLine("NameChanged -> " + ((Person)sender).Name);
    }

    static void Main()
    {
        Type t = typeof(Person);
        PropertyInfo p = t.GetProperty("Name");
        CategoryAttribute c = (CategoryAttribute)Attribute
            .GetCustomAttribute(p, typeof(CategoryAttribute));
        Console.WriteLine("property " + p.Name + " [" + c.Category
            + "] get=" + p.GetGetMethod().Name);
        EventInfo e = t.GetEvent("NameChanged");
        Console.WriteLine("event " + e.Name + " add="
            + e.GetAddMethod().Name);

        Person x = new Person();
        x.NameChanged += new EventHandler(Changed);
        x.Name = "Ada";
    }
}
