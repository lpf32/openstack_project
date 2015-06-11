$(function(){

	/*图标手风琴效果*/
	$(".icon-title").each(function(){

		$(this).click(function(){
			if($(this).next(".lct-icon").css("display")== "none")
			{
				$(this).next(".lct-icon").slideDown();
			}
			else
			{
				$(this).next(".lct-icon").slideUp();
			}
		});

	});
	/*图标手风琴效果*/

	//自适应高度
	var wheight = $(window).height()-43.5;
	$(".topo-left").css("height",wheight);
	$(".topo-right").css("height",wheight);

	//创建
	art("#new-btn").dialog({
		id: 'win1',
		title: '创建',
		content: $("#new-win").html(),
		follow: $('#new-btn'),
		resize:false,
		lock:true,
		button: [
			{
				name: '提交',
				callback: function () {
					$("#new-form").submit();
				},
				focus: true
			},
			{
				name: '关闭'
			}
		]
	});

	//导入
	art("#prop-btn").dialog({
		id: 'win2',
		title: '导入',
		content: $("#prop-win").html(),
		follow: $('#prop-btn'),
		resize:false,
		lock:true,
		button: [
			{
				name: '提交',
				callback: function () {
					$("#prop-form").submit();
				},
				focus: true
			},
			{
				name: '关闭'
			}
		]
	});
	
	$(".action-select").change(function(){

		var i = $(this).val();
		
		if(i == 1)//挂载
		{
			
			art.dialog({
				id: 'win4',
				title: '挂载',
				content: $("#location-win").html(),
				lock:true,
				resize:false,
				button: [
					{
						name: '提交',
						callback: function () {
							$("#action-form").submit();
						},
						focus: true
					},
					{
						name: '关闭'
					}
				]
			});

		}
		else if(i == 2) //卸载
		{
			var listid = $(this).next(".list-id").val();

			$.ajax({
				type: "POST",
				url: "action/xz.html",
				data: {'id':listid},
				cache:false,
				beforeSend:function(){
					if(!confirm("确认要删除？"))
					{
						return false;
					}
				},
				success: function(data){
					$("#eq-area").html(data);
				}
			});

		}

	});

	//搜索挂载
	$("#gz-search").live("click",function(){

		var name = $("#gz-search-name").val();
		var ip = $("#gz-search-ip").val(); 

		$.ajax({
			type: "POST",
			url: "get_vms/",
			data: {'name':name,'ip':ip},
			cache:false,
			success: function(data){
				//$("#action-form").html(data);
				alert(data);
				console.log("success");
			}
		});

	});

});
